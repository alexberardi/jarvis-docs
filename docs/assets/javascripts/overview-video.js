// Keep each poster as a working YouTube link without JavaScript. No player or
// third-party thumbnail is fetched until someone chooses to watch.
// A poster is <a class="overview-poster" href="https://youtu.be/ID" data-title="…" data-label="…">.
(function () {
  document.querySelectorAll("a.overview-poster").forEach(function (poster) {
    var id = poster.pathname.split("/").pop();
    var title = poster.dataset.title || "Video";

    var button = document.createElement("button");
    button.type = "button";
    button.className = poster.className;
    button.setAttribute("aria-label", poster.dataset.label || "Watch on YouTube");
    while (poster.firstChild) button.appendChild(poster.firstChild);
    poster.replaceWith(button);

    button.addEventListener("click", function () {
      var frame = document.createElement("iframe");
      frame.title = title;
      frame.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) + "?autoplay=1&playsinline=1&rel=0";
      frame.allow = "autoplay; encrypted-media; picture-in-picture; fullscreen";
      frame.allowFullscreen = true;
      frame.referrerPolicy = "strict-origin-when-cross-origin";
      button.replaceWith(frame);
      frame.focus();
    });
  });
})();
