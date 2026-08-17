document.addEventListener("DOMContentLoaded", () => {
    // Smooth reveal for major sections.
    document.querySelectorAll(".hero, .feature, .card, .stat, .files-card").forEach((el, index) => {
        el.classList.add("reveal");
        if (index % 3 === 1) el.classList.add("delay-1");
        if (index % 3 === 2) el.classList.add("delay-2");
    });

    // Auto-dismiss flash/toast messages.
    document.querySelectorAll(".toast").forEach((toast) => {
        setTimeout(() => {
            toast.style.transition = "opacity .3s ease, transform .3s ease";
            toast.style.opacity = "0";
            toast.style.transform = "translateY(-8px)";
            setTimeout(() => toast.remove(), 320);
        }, 4200);
    });

    // Premium password visibility toggle.
    document.querySelectorAll(".toggle-password").forEach((button) => {
        button.addEventListener("click", () => {
            const input = document.getElementById(button.dataset.target);
            if (!input) return;
            input.type = input.type === "password" ? "text" : "password";
            button.setAttribute("aria-label", input.type === "password" ? "Show password" : "Hide password");
        });
    });

    // Drag-and-drop upload interaction.
    const dropzone = document.querySelector(".dropzone");
    const fileInput = document.querySelector("#file");
    const selected = document.querySelector(".file-selected");

    if (dropzone && fileInput) {
        ["dragenter", "dragover"].forEach((eventName) => {
            dropzone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropzone.classList.add("dragging");
            });
        });

        ["dragleave", "drop"].forEach((eventName) => {
            dropzone.addEventListener(eventName, (event) => {
                event.preventDefault();
                dropzone.classList.remove("dragging");
            });
        });

        dropzone.addEventListener("drop", (event) => {
            if (event.dataTransfer.files.length) {
                fileInput.files = event.dataTransfer.files;
                showSelectedFile();
            }
        });

        fileInput.addEventListener("change", showSelectedFile);

        function showSelectedFile() {
            if (!selected || !fileInput.files.length) return;
            const file = fileInput.files[0];
            const size = file.size < 1024 * 1024
                ? `${(file.size / 1024).toFixed(1)} KB`
                : `${(file.size / (1024 * 1024)).toFixed(2)} MB`;
            selected.textContent = `✓ ${file.name} · ${size}`;
        }
    }
});
