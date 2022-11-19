const connect = document.getElementById('btnc')

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