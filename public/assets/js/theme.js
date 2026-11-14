// Theme switch: System / Light / Dark.
// The choice is applied before first paint by the small inline script in each
// page's <head>; this file only wires up the buttons. No choice stored = follow
// the operating system (prefers-color-scheme), handled entirely in CSS.
(function () {
  var root = document.documentElement;
  var KEY = "theme";
  var group = document.querySelector(".theme-switch");
  if (!group) return;
  var buttons = group.querySelectorAll("button[data-theme-choice]");

  function current() {
    return root.getAttribute("data-theme") || "system";
  }

  function sync() {
    var c = current();
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].setAttribute("aria-pressed", String(buttons[i].getAttribute("data-theme-choice") === c));
    }
  }

  function apply(choice) {
    if (choice === "light" || choice === "dark") {
      root.setAttribute("data-theme", choice);
    } else {
      root.removeAttribute("data-theme");
    }
    try {
      if (choice === "light" || choice === "dark") localStorage.setItem(KEY, choice);
      else localStorage.removeItem(KEY);
    } catch (e) { /* storage blocked: the choice lasts for this page only */ }
    sync();
  }

  group.addEventListener("click", function (event) {
    var button = event.target.closest("button[data-theme-choice]");
    if (button) apply(button.getAttribute("data-theme-choice"));
  });

  group.hidden = false; // hidden in the HTML so it never shows without JavaScript
  sync();
})();
