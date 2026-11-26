// #<theme>-<pace>, e.g. #light-push: the theme and the pace word with the status bar's icon
const [theme, pace = "steady"] = location.hash.slice(1).split("-");
if (theme === "light") document.documentElement.dataset.theme = "light";
document.documentElement.dataset.pace = pace;
const icon = { push: "▲", steady: "•", slow: "▼" }[pace];
document.querySelectorAll("[data-word]").forEach((el) => { el.textContent = `${icon} ${pace}`; });
