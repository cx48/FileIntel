function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem("theme", document.body.classList.contains("dark") ? "dark" : "light");
}
window.onload = function () {
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
        document.body.classList.add("dark");
    }
};
document.getElementById("search").addEventListener("input", function() {
    const query = this.value.toLowerCase();
    document.querySelectorAll(".meta").forEach(entry => {
        const text = entry.innerText.toLowerCase();
        entry.style.display = text.includes(query) ? "" : "none";
    });
});