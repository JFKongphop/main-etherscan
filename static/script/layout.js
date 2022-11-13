const connect = document.getElementById('btnc')
const thisAddress = document.getElementById('thisAddress')
// const formData = document.getElementById('formData')
// const inputc = document.getElementById('inputc')
// const search = document.querySelector('.searchc')

let address = ""

connect.addEventListener('click', ()=>{
    getAccount()
    console.log("connect");
})

async function getAccount() {
    const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
    const account = accounts[0];
    if (account[0]){
        const lessAccount = account.slice(0,5)+"...."+account.slice(37,42);
        localStorage.setItem("address", lessAccount)
        connect.innerHTML = localStorage.getItem("address")
    }
    else{
        connect.innerHTML = "Fail"
    }
}


// formData.addEventListener("change", ()=>{
//     address = inputc.value
//     if(address){
//         search.addEventListener('click', ()=>{
//             if(!address){
//                 alert("Please enter address")
                
//             }
//         })
//     }
//     else{
//         window.location.reload()
//     }
// })





// formData.addEventListener('submit', (e)=>{
//     e.preventDefault()
//     if (!thisAddress.value){
//         alert("Please enter address")
//     }
// })