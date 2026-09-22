from imports import *
from blueprints.weight_ms import round_to_nearest_even, get_ideal_weight, compute_authorization

weight_graph_bp = Blueprint('weight_graph', __name__, url_prefix='/weight_graph')

JCO_RANKS = ("Naib Subedar", "Subedar", "Subedar Major")

@weight_graph_bp.route('/api/graph-personnel', methods=['GET'])
def get_graph_personnel():
    """
    Returns personnel list for a clicked segment of any weight system graph.
    Parameters:
      - graph_type: 'fit_unfit', 'shape_category', 'jco_or_fit', 'jco_or_shape'
      - slice_label: label of clicked slice (e.g. 'Fit', 'Unfit', 'Shape I', 'LMC', 'JCO Fit', 'OR Fit', etc.)
      - company: company name or 'All'
      - fitUnfitFilter: 'Fit' or 'Unfit' (for jco_or_fit chart)
      - safeCategoryFilter: 'shape' or 'category' (for jco_or_shape chart)
    """
    user = require_login()
    user_company = user.get('company', '').strip() if (user and isinstance(user, dict)) else ''

    req_company = request.args.get('company', 'All').strip()
    graph_type = request.args.get('graph_type', '').strip()
    slice_label = request.args.get('slice_label', '').strip()
    fit_unfit_filter = request.args.get('fitUnfitFilter', 'Fit').strip()
    safe_category_filter = request.args.get('safeCategoryFilter', 'shape').strip()

    # Admin check: if user is not Admin/2IC/Center, lock company to user_company
    ADMIN_ROLES = ["Admin", "2IC", "Center"]
    if user_company and user_company not in ADMIN_ROLES:
        effective_company = user_company
    else:
        effective_company = req_company

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get weight_info computed authorization data for height/weight/ideal_weight/status
        all_computed = compute_authorization(effective_company)
        
        # Build lookup for computed status (Fit/UnFit, ideal_weight, deviation) by army_number
        computed_dict = { item['army_number']: item for item in all_computed }

        # Query weight_info table for full records
        if effective_company and effective_company != "All":
            cursor.execute("""
                SELECT 
                    army_number, name, company, `rank`, age, height AS height_cm, 
                    actual_weight, status_type, category_type, restrictions
                FROM weight_info
                WHERE company = %s
                ORDER BY name
            """, (effective_company,))
        else:
            cursor.execute("""
                SELECT 
                    army_number, name, company, `rank`, age, height AS height_cm, 
                    actual_weight, status_type, category_type, restrictions
                FROM weight_info
                ORDER BY name
            """)

        raw_rows = cursor.fetchall()

        # Merge raw_rows with computed_dict
        full_rows = []
        for r in raw_rows:
            army_no = r['army_number']
            comp = computed_dict.get(army_no, {})

            age = r['age']
            height_cm = round_to_nearest_even(r['height_cm']) if r.get('height_cm') is not None else 0
            actual_weight = r.get('actual_weight')

            ideal_weight = comp.get('ideal_weight') or get_ideal_weight(age, height_cm, cursor)
            status = comp.get('status') or ("Fit" if (ideal_weight and actual_weight is not None and ideal_weight * 0.88 <= actual_weight <= ideal_weight * 1.12) else "UnFit")
            weight_dev_kg = comp.get('weight_deviation_kg', 0)
            weight_dev_pct = comp.get('weight_deviation_percent', 0)

            full_rows.append({
                "army_number": r['army_number'],
                "name": r['name'],
                "rank": r['rank'] or "N/A",
                "company": r['company'] or "N/A",
                "age": age,
                "height_cm": r['height_cm'],
                "actual_weight": actual_weight,
                "ideal_weight": ideal_weight,
                "weight_deviation_kg": weight_dev_kg,
                "weight_deviation_percent": weight_dev_pct,
                "status": status,
                "status_type": r.get('status_type') or "shape",
                "category_type": r.get('category_type') or "N/A",
                "restrictions": r.get('restrictions') or ""
            })

        # Filter full_rows based on graph_type & slice_label
        filtered_rows = []
        label_lower = slice_label.lower().strip()

        if graph_type == 'fit_unfit':
            if 'unfit' in label_lower:
                filtered_rows = [r for r in full_rows if r['status'].lower() == 'unfit']
            else:
                filtered_rows = [r for r in full_rows if r['status'].lower() == 'fit']

        elif graph_type == 'shape_category':
            if 'lmc' in label_lower or 'category' in label_lower:
                filtered_rows = [r for r in full_rows if r['status_type'].lower() == 'category']
            else:
                filtered_rows = [r for r in full_rows if r['status_type'].lower() == 'shape']

        elif graph_type == 'jco_or_fit':
            target_status = fit_unfit_filter.lower()
            is_jco_target = 'jco' in label_lower
            jco_ranks_lower = [x.lower() for x in JCO_RANKS]

            if is_jco_target:
                filtered_rows = [
                    r for r in full_rows 
                    if r['status'].lower() == target_status 
                    and (r['rank'] or '').strip().lower() in jco_ranks_lower
                ]
            else:
                filtered_rows = [
                    r for r in full_rows 
                    if r['status'].lower() == target_status 
                    and (r['rank'] or '').strip().lower() not in jco_ranks_lower
                ]

        elif graph_type == 'jco_or_shape':
            target_status_type = safe_category_filter.lower()
            is_jco_target = 'jco' in label_lower
            jco_ranks_lower = [x.lower() for x in JCO_RANKS]

            if is_jco_target:
                filtered_rows = [
                    r for r in full_rows 
                    if r['status_type'].lower() == target_status_type 
                    and (r['rank'] or '').strip().lower() in jco_ranks_lower
                ]
            else:
                filtered_rows = [
                    r for r in full_rows 
                    if r['status_type'].lower() == target_status_type 
                    and (r['rank'] or '').strip().lower() not in jco_ranks_lower
                ]
        else:
            filtered_rows = full_rows

        return jsonify({
            "status": "success",
            "graph_type": graph_type,
            "slice_label": slice_label,
            "company": effective_company,
            "count": len(filtered_rows),
            "rows": filtered_rows
        })

    except Exception as e:
        print("Error in graph personnel details:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
