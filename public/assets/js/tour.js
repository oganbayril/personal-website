// Dashboard tour video (EU page): it autoplays muted, unless the visitor has
// asked for reduced motion; then it stays on its first frame until they press play.
(function () {
  var video = document.querySelector(".tour-video video");
  if (!video || !window.matchMedia) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    video.removeAttribute("autoplay");
    video.pause();
    try { video.currentTime = 0; } catch (e) { /* not seekable yet: already at 0 */ }
  }
})();
