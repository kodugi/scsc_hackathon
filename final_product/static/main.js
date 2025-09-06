const handle = document.getElementById("handle");
const loginBtn = document.getElementById("loginBtn");
const profileNav = document.getElementById("profile_nav");
const loginNav = document.getElementById("login_nav");
const tab_home = document.getElementById("home");
const tab_question = document.getElementById("search_question");
const problems = document.getElementById("problems");

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
    });
    
    fetch('getRecommendation')
    .then((response) => {
        return response.json();
    })
    .then((data => {
        const items = data.items;
        items.forEach(element => {
            const item = document.createElement("div");
            item.className = "problem";
            const no = document.createElement("p");
            no.textContent = element["problemId"];
            const title = document.createElement("a");
            title.text = element["titleKo"];
            title.href = "https://www.acmicpc.net/problem/" + element["problemId"];
            item.appendChild(no);
            item.appendChild(title);
            problems.appendChild(item);
        });
    }))
};