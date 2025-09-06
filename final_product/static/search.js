const tag = document.getElementById("tag");
const submit = document.getElementById("submit");
const problems = document.getElementById("problems")

window.onload = () => {
    fetch('/getTagList')
    .then(response => {
        return response.json();
    })
    .then(data => {
        data.items.forEach(element => {
            const item = document.createElement("option");
            item.value = element["en"]
            item.text = element["ko"]
            tag.appendChild(item)
        });
    })
};

submit.addEventListener('click', () => {
    problems.innerHTML = ""
    console.log("chosen: ", tag.options[tag.selectedIndex].value)
    const dataToSend = {
        'tag': tag.options[tag.selectedIndex].value
    };
    fetch('/getRecommendationByTag', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataToSend)
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
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
    });
});