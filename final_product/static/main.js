const handle = document.getElementById("handle");
const loginBtn = document.getElementById("loginBtn");
const profileNav = document.getElementById("profile_nav");
const loginNav = document.getElementById("login_nav");

var loginInfo;

window.onload = () => {
    fetch('/getLogin')
    .then((response) => {
        return response.json();
    })
    .then(data => {
        loginInfo = data.items;
        console.log(loginInfo);
        if(loginInfo[0] === true){
            loginNav.style.display = 'none';
            profileNav.style.display = 'block';
        }
        else{
            loginNav.style.display = 'block';
            profileNav.style.display = 'none';
        }
        document.getElementById("handle").innerHTML = loginInfo[1];
    })
    

    
};