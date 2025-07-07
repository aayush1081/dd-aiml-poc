(function () {
  const scripts = document.querySelectorAll('script[src*="chatbot-widget.js"]');
  const script = scripts[scripts.length - 1];
  const urlParams = new URLSearchParams(script.src.split("?")[1]);
  const config = JSON.parse(urlParams.get("config") || "{}");

  const container = document.createElement("div");
  container.style.cssText = "position:fixed;bottom:20px;right:20px;padding:10px;background:#f5f5f5;border:1px solid #ccc;border-radius:8px;z-index:9999;font-family:sans-serif";
  container.innerHTML = `<strong>You:</strong> ${config.initial_message || "Hello"}<br><em>Loading...</em>`;
  document.body.appendChild(container);

  const messages = [{ role: "user", content: config.initial_message || "Hello" }];

  fetch("http://localhost:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, ip: "0.0.0.0" }) 
  })
    .then(res => res.json())
    .then(data => {
      container.innerHTML += `<br><strong>Bot:</strong> ${data.response}`;
    })
    .catch(err => {
      container.innerHTML += "<br><strong>Error:</strong> Unable to connect to chatbot.";
      console.error(err);
    });
})();
