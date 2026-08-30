document.addEventListener("DOMContentLoaded", () => {
  // 1. Scroll Progress Bar
  const progressBar = document.createElement("div");
  progressBar.className = "scroll-progress-bar";
  document.body.prepend(progressBar);

  const updateProgress = () => {
    const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
    if (totalHeight > 0) progressBar.style.width = `${(window.scrollY / totalHeight) * 100}%`;
  };
  window.addEventListener("scroll", updateProgress, { passive: true });

  // 2. IntersectionObserver for Reveal Elements
  const revealElements = document.querySelectorAll(".reveal");
  if (revealElements.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) entry.target.classList.add("is-visible");
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
    revealElements.forEach((el) => observer.observe(el));
  }

  // 3. Dynamic Time-Based Greeting
  const greetingElement = document.getElementById("dynamic-greeting");
  if (greetingElement) {
    const hour = new Date().getHours();
    const timeOfDay = hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
    greetingElement.textContent = `Good ${timeOfDay}, ${greetingElement.dataset.username || "there"}.`;
  }

  // 4. Live AES-256 Ciphertext Animation Stream
  const ciphertextStream = document.getElementById("ciphertext-stream");
  const hexChars = "0123456789ABCDEF";
  const generateHex = (length) => Array.from({ length }, () => hexChars[Math.floor(Math.random() * hexChars.length)]).join("");
  if (ciphertextStream) {
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
          } else progressStatus.textContent = `Preparing encryption... ${progress}%`;
          progressFill.style.width = `${progress}%`;
        }, 80);
      }
    };
    input.addEventListener("change", (e) => handleFileSelection(e.target.files?.[0]));
    ["dragenter", "dragover"].forEach((evt) => zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.add("dragging"); }));
    ["dragleave", "drop"].forEach((evt) => zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.remove("dragging"); }));
    zone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files.length) {
        input.files = e.dataTransfer.files;
        handleFileSelection(e.dataTransfer.files[0]);
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

  // 8. Secure Decrypt & Download flow
  const decryptDownloadModalElement = document.getElementById("decryptDownloadModal");
  const decryptDownloadForm = document.getElementById("decryptDownloadForm");
  const decryptDownloadPassword = document.getElementById("decryptDownloadPassword");
  const decryptDownloadDocumentName = document.getElementById("decryptDownloadDocumentName");
  const toggleDecryptPassword = document.getElementById("toggleDecryptPassword");
  const decryptDownloadError = document.getElementById("decryptDownloadError");
  const decryptDownloadSubmit = decryptDownloadForm?.querySelector('button[type="submit"]');

  const showDecryptError = (message) => {
    if (decryptDownloadError) {
      decryptDownloadError.textContent = `⚠️ ${message}`;
      decryptDownloadError.classList.remove("d-none");
    }
  };

  document.querySelectorAll(".decrypt-download-trigger").forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      if (!decryptDownloadModalElement || !decryptDownloadForm || typeof bootstrap === "undefined") return;
      event.preventDefault();

      decryptDownloadForm.action = trigger.dataset.downloadUrl || trigger.href;
      decryptDownloadForm.reset();
      decryptDownloadForm.removeAttribute("data-submitting");
      if (decryptDownloadError) decryptDownloadError.classList.add("d-none");
      if (decryptDownloadSubmit) {
        decryptDownloadSubmit.disabled = false;
        decryptDownloadSubmit.style.opacity = "1";
      }

      if (decryptDownloadDocumentName) {
        decryptDownloadDocumentName.textContent = trigger.dataset.documentName || "Selected document";
      }

      const modal = bootstrap.Modal.getOrCreateInstance(decryptDownloadModalElement);
      modal.show();
      decryptDownloadModalElement.addEventListener("shown.bs.modal", () => decryptDownloadPassword?.focus(), { once: true });
    });
  });

  // Handle decryption with fetch so a failed POST/redirect can NEVER be treated
  // by the browser as a file download. Only an explicit successful attachment
  // response is converted to a downloadable Blob.
  if (decryptDownloadForm) {
    decryptDownloadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (decryptDownloadForm.dataset.submitting === "true") return;

      const password = decryptDownloadPassword?.value || "";
      if (!password) {
        showDecryptError("A document password is required.");
        return;
      }

      decryptDownloadForm.dataset.submitting = "true";
      if (decryptDownloadSubmit) {
        decryptDownloadSubmit.disabled = true;
        decryptDownloadSubmit.textContent = "Decrypting…";
      }
      if (decryptDownloadError) decryptDownloadError.classList.add("d-none");

      try {
        const response = await fetch(decryptDownloadForm.action, {
          method: "POST",
          body: new FormData(decryptDownloadForm),
          credentials: "same-origin",
          cache: "no-store",
          redirect: "follow",
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });

        const contentType = (response.headers.get("Content-Type") || "").toLowerCase();
        const disposition = response.headers.get("Content-Disposition") || "";

        // A valid download must be a successful attachment response. HTML is
        // always treated as an error/flash response, never as a file.
        const isDownload = response.ok && disposition.toLowerCase().includes("attachment") && !contentType.includes("text/html");
        if (!isDownload) {
          let message = "Unable to decrypt the document. Please check the password and try again.";
          try {
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");
            const flash = doc.querySelector(".flash.error, .flash.alert-danger");
            if (flash?.textContent?.trim()) message = flash.textContent.trim();
          } catch (_) {
            // Keep the safe generic message when the response cannot be parsed.
          }
          showDecryptError(message.replace(/^⚠️\s*/, ""));
          decryptDownloadForm.dataset.submitting = "false";
          if (decryptDownloadSubmit) {
            decryptDownloadSubmit.disabled = false;
            decryptDownloadSubmit.textContent = "Decrypt & Download";
          }
          decryptDownloadPassword?.focus();
          decryptDownloadPassword?.select();
          return;
        }

        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = objectUrl;
        anchor.download = decryptDownloadDocumentName?.textContent || "download";
        document.body.appendChild(anchor);
        anchor.click();
        anchor.remove();
        URL.revokeObjectURL(objectUrl);

        decryptDownloadForm.dataset.submitting = "false";
        if (decryptDownloadSubmit) {
          decryptDownloadSubmit.disabled = false;
          decryptDownloadSubmit.textContent = "Decrypt & Download";
        }
      } catch (_) {
        showDecryptError("The download could not be completed. Please try again.");
        decryptDownloadForm.dataset.submitting = "false";
        if (decryptDownloadSubmit) {
          decryptDownloadSubmit.disabled = false;
          decryptDownloadSubmit.textContent = "Decrypt & Download";
        }
      }
    });
  }

  if (toggleDecryptPassword && decryptDownloadPassword) {
    toggleDecryptPassword.addEventListener("click", () => {
      const visible = decryptDownloadPassword.type === "text";
      decryptDownloadPassword.type = visible ? "password" : "text";
      toggleDecryptPassword.textContent = visible ? "Show" : "Hide";
      toggleDecryptPassword.setAttribute("aria-label", visible ? "Show password" : "Hide password");
    });
  }

  // 9. Install SecureVault popup — home page only, once per browser session.
  let deferredInstallPrompt = null;
  const installModalElement = document.getElementById("installAppModal");
  const installButton = document.getElementById("installAppButton");
  const isStandalone = window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  const isHomePage = window.location.pathname === "/";
  const installShownThisSession = sessionStorage.getItem("secureVaultInstallShown_v3") === "true";

  const showInstallModal = () => {
    if (!installModalElement || isStandalone || !isHomePage || installShownThisSession || !deferredInstallPrompt) return;
    sessionStorage.setItem("secureVaultInstallShown_v3", "true");
    if (typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(installModalElement).show();
  };

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    showInstallModal();
  });

  if (installButton) {
    installButton.addEventListener("click", async () => {
      if (!deferredInstallPrompt) return;

      deferredInstallPrompt.prompt();
      const result = await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;

      if (result.outcome === "accepted" && typeof bootstrap !== "undefined") {
        bootstrap.Modal.getOrCreateInstance(installModalElement).hide();
      }
    });
  }

  window.addEventListener("appinstalled", () => {
    deferredInstallPrompt = null;
    if (installModalElement && typeof bootstrap !== "undefined") {
      bootstrap.Modal.getOrCreateInstance(installModalElement).hide();
    }
  });
});
