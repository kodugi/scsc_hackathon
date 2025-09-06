const tag = document.getElementById("tag");

window.onload = () => {
    fetch('/getTagList')
    .then(response => {
        return response.json();
    })
    .then(data => {
        const item = new Option();
        item.value = "no_choice";
        item.text = "선택 안함";
        tag.append(item)
        data.items.forEach(element => {
            const item = new Option();
            console.log(element["ko"]);
            item.value = element["en_short"];
            item.text = element["ko"];
            tag.append(item)
        });
    })
};