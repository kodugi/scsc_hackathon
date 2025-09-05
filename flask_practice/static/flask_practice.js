const btn = document.getElementById("btn");
const list = document.getElementById("ulist");
console.log(list.innerHTML);
btn.addEventListener('click', () => {
    fetch('/run_python')
    .then(response => response.json())
    .then(data => {
        console.log(data.items);
        data.items.forEach(element => {
            console.log(element);
            const nli = document.createElement("li");
            const txt = document.createTextNode(element);
            nli.appendChild(txt);
            list.appendChild(nli);
        });
        
    });
});