const tag = document.getElementById("tag");

window.onload = () => {
    fetch('/getTagList')
    .then(response => {
        return response.json();
    })
    .then(data => {
        data.items.forEach(element => {
            const item = document.createElement("option");
            item.setAttribute("value", element)
        });
    })
};