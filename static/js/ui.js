document.addEventListener("DOMContentLoaded", () => {
  // 1. Scroll Progress Bar
  const progressBar = document.createElement("div");
  progressBar.className = "scroll-progress-bar";
  document.body.prepend(progressBar);

  const updateProgress = () => {
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (totalHeight > 0) {
      const progress = (window.scrollY / totalHeight) * 100;
      progressBar.style.width = `${progress}%`;
    }
  };
  window.addEventListener("scroll", updateProgress, { passive: true });

  // 2. IntersectionObserver for Reveal Elements
  const revealElements = document.querySelectorAll(".reveal");
  if (revealElements.length > 0) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
    );
    revealElements.forEach((el) => observer.observe(el));
  }

  // 3. Dynamic Time-Based Greeting Generator
  const greetingElement = document.getElementById("dynamic-greeting");
  if (greetingElement) {
    const hour = new Date().getHours();
    let timeOfDay = "day";
    if (hour < 12) timeOfDay = "morning";
    else if (hour < 17) timeOfDay = "afternoon";
    else timeOfDay = "evening";

    const userName = greetingElement.dataset.username || "there";
    greetingElement.textContent = `Good ${timeOfDay}, ${userName}.`;
  }

  // 4. Live AES-256 Ciphertext Animation Stream (Landing Page Demo)
  const ciphertextStream = document.getElementById("ciphertext-stream");
  if (ciphertextStream) {
    const hexChars = "0123456789ABCDEF";
    const generateHex = (length) => {
      let result = "";
      for (let i = 0; i < length; i++) {
        result += hexChars.charAt(Math.floor(Math.random() * hexChars.length));
      }
      return result;
    };

    setInterval(() => {
      ciphertextStream.textContent = `8F3A91${generateHex(10)}...${generateHex(4)}\n${generateHex(8)}A91F${generateHex(8)}\n7C12${generateHex(12)}`;
    }, 400);
  }

  // 5. File Dropzone & Live Encryption Progress
  document.querySelectorAll(".dropzone").forEach((zone) => {
    const input = zone.querySelector('input[type="file"]');
    const banner = zone.parentElement.querySelector(".selected-file-banner");
    const fileNameEl = banner?.querySelector(".selected-file-name");
    const fileSizeEl = banner?.querySelector(".selected-file-size");
    const progressContainer = zone.parentElement.querySelector(".progress-bar-container");
    const progressFill = progressContainer?.querySelector(".progress-bar-fill");
    const progressStatus = progressContainer?.querySelector(".progress-status-text");

    if (!input) return;

    const handleFileSelection = (file) => {
      if (!file) return;

      if (banner && fileNameEl && fileSizeEl) {
        fileNameEl.textContent = file.name;
        fileSizeEl.textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
        banner.classList.add("active");
      }

      if (progressContainer && progressFill && progressStatus) {
        progressContainer.classList.add("active");
        let progress = 0;
        const interval = setInterval(() => {
          progress += Math.floor(Math.random() * 18) + 10;
          if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            progressStatus.textContent = "Ready for AES-256 encryption ✓";
          } else {
            progressStatus.textContent = `Preparing encryption... ${progress}%`;
          }
          progressFill.style.width = `${progress}%`;
        }, 80);
      }
    };

    input.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      handleFileSelection(file);
    });

    ["dragenter", "dragover"].forEach((evt) => {
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.add("dragging");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      zone.addEventListener(evt, (e) => {
        e.preventDefault();
        zone.classList.remove("dragging");
      });
    });

    zone.addEventListener("drop", (e) => {
      const files = e.dataTransfer.files;
      if (files.length) {
        input.files = files;
        handleFileSelection(files[0]);
      }
    });
  });

  // 6. Show / Hide Password Toggle
  document.querySelectorAll(".toggle-pw").forEach((button) => {
    button.addEventListener("click", () => {
      const input = document.getElementById(button.dataset.target);
      if (!input) return;
      const isPw = input.type === "password";
      input.type = isPw ? "text" : "password";
      button.textContent = isPw ? "🙈" : "👁";
      button.setAttribute("aria-label", isPw ? "Hide password" : "Show password");
    });
  });

  // 7. Form Lock Prevention & Submit Feedback
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", () => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.dataset.submitting) {
        submitBtn.dataset.submitting = "true";
        submitBtn.style.opacity = "0.75";
      }
    });
  });
});
