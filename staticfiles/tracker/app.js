(function () {
  const button = document.getElementById("enable-notifications");
  if (button) {
    button.addEventListener("click", async () => {
      if (!("Notification" in window)) {
        alert("This browser does not support notifications. You can still view your schedule in the dashboard.");
        return;
      }
      const permission = await Notification.requestPermission();
      if (permission === "granted") {
        new Notification("MediSmart alerts enabled", { body: "Keep this dashboard open for in-page reminder checks." });
        button.textContent = "Browser alerts enabled";
        button.disabled = true;
        startReminderChecks();
      } else {
        alert("Notifications were not enabled. You can change browser permissions in settings.");
      }
    });
  }

  function startReminderChecks() {
    // This is a foreground-only demo: checks run while this page remains open.
    // It is NOT a guaranteed alarm when the browser/device is closed.
    const rows = Array.from(document.querySelectorAll("[data-reminder-time]"));
    const sent = new Set();
    function check() {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const current = `${hh}:${mm}`;
      rows.forEach((row) => {
        const key = `${new Date().toDateString()}-${row.dataset.reminderName}-${current}`;
        if (row.dataset.reminderTime === current && !sent.has(key) && Notification.permission === "granted") {
          new Notification("Medicine reminder", {
            body: `Check your saved schedule for: ${row.dataset.reminderName}`,
            tag: key
          });
          sent.add(key);
        }
      });
    }
    check();
    window.setInterval(check, 15000);
  }
})();
