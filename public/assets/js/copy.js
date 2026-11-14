// "Copy address" buttons: <button data-copy-target="ID"> copies the text of #ID.
// Clipboard API first; if that is missing or refused, select the text so the
// visitor can copy it with the keyboard. The result is announced in the
// role="status" element next to the button. Buttons are hidden in the HTML so
// they never show without JavaScript.
(function () {
  var buttons = document.querySelectorAll("button[data-copy-target]");
  var isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);

  function selectText(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  Array.prototype.forEach.call(buttons, function (button) {
    var target = document.getElementById(button.getAttribute("data-copy-target"));
    var status = button.parentNode.querySelector("[role=status]");
    if (!target || !status) return;
    var timer;

    function say(message, ms) {
      clearTimeout(timer);
      status.textContent = message;
      timer = setTimeout(function () { status.textContent = ""; }, ms);
    }

    function fallback() {
      selectText(target);
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { /* not supported */ }
      if (ok) say("Copied", 2000);
      else say("Selected: press " + (isMac ? "⌘C" : "Ctrl+C") + " to copy", 6000);
    }

    button.addEventListener("click", function () {
      var text = target.textContent.trim();
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { say("Copied", 2000); }, fallback);
      } else {
        fallback();
      }
    });

    button.hidden = false;
  });
})();
