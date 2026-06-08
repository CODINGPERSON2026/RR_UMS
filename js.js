async function getAll(){

    try {

        res  =  await fetch('https://jsonplaceholder.typicode.com/users')
        resultData = await res.json()
       userResult  = resultData.find((user)=>{
        return  user.name ===  'Clementine Bauch'
       })
        console.log(userResult)
    } catch (error) {
        console.log(error)
    }
}


getAll()