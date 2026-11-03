(function () {
  function mark(id, text, ok) {
    var el = document.getElementById(id);
    el.textContent = text;
    el.classList.toggle("ok", ok);
  }
  var css = getComputedStyle(document.getElementById("css-status")).getPropertyValue("--css-loaded").trim();
  mark("css-status", css === "yes" ? "styled" : "styles missing", css === "yes");
  var img = document.getElementById("badge");
  function imgDone() {
    var ok = img.complete && img.naturalWidth > 0;
    mark("img-status", ok ? "loaded" : "failed", ok);
  }
  if (img.complete) imgDone(); else { img.addEventListener("load", imgDone); img.addEventListener("error", imgDone); }
  mark("js-status", "running", true);
  document.body.dataset.deliveryCheck = "ready";
})();
