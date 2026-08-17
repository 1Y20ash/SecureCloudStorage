document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".dropzone").forEach((zone) => {
        const input = zone.querySelector('input[type="file"]');
        const selected = zone.querySelector(".file-selected");
        if (!input) return;

        const update = () => {
            const file = input.files?.[0];
            if (!selected) return;
            selected.textContent = file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB` : "";
            zone.classList.toggle("has-file", Boolean(file));
        };

        input.addEventListener("change", update);
        ["dragenter", "dragover"].forEach((eventName) => zone.addEventListener(eventName, (event) => {
            event.preventDefault();
            zone.classList.add("dragging");
        }, { passive: false }));
        ["dragleave", "drop"].forEach((eventName) => zone.addEventListener(eventName, (event) => {
            event.preventDefault();
            zone.classList.remove("dragging");
        }, { passive: false }));
        zone.addEventListener("drop", (event) => {
            const files = event.dataTransfer.files;
            if (files.length) {
                input.files = files;
                update();
            }
        });
    });

    document.querySelectorAll(".toggle-password").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.target);
            if (!input) return;
            input.type = input.type === "password" ? "text" : "password";
            button.setAttribute("aria-label", input.type === "password" ? "Show password" : "Hide password");
        });
    });

    document.querySelectorAll("form").forEach((form) => {
        form.addEventListener("submit", () => {
            const submit = form.querySelector('button[type="submit"]:not(.toggle-password)');
            if (!submit || form.dataset.confirmed === "true") return;
            if (submit.dataset.locked === "true") return;
            submit.dataset.locked = "true";
            submit.classList.add("is-loading");
            submit.setAttribute("aria-busy", "true");
        });
    });
});
