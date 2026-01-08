document.addEventListener("DOMContentLoaded", () => {
  // ----- Tabs -----
  const tabStep1 = document.getElementById("tabStep1");
  const tabStep2 = document.getElementById("tabStep2");
  const panelStep1 = document.getElementById("panelStep1");
  const panelStep2 = document.getElementById("panelStep2");

  function setActiveTab(step) {
    const isStep1 = step === 1;
    panelStep1.classList.toggle("hidden", !isStep1);
    panelStep2.classList.toggle("hidden", isStep1);
    const active = "bg-blue-600 text-white border-blue-600";
    const inactive = "bg-white text-gray-800 border-gray-300 hover:bg-gray-50";
    tabStep1.className = `px-4 py-2 rounded-lg font-semibold border transition ${
      isStep1 ? active : inactive
    }`;
    tabStep2.className = `px-4 py-2 rounded-lg font-semibold border transition ${
      !isStep1 ? active : inactive
    }`;
  }

  tabStep1.addEventListener("click", () => setActiveTab(1));
  tabStep2.addEventListener("click", () => setActiveTab(2));
  setActiveTab(1);

  // ----- Modal Logic -----
  const modal = document.getElementById("validationModal");
  const tableBody = document.getElementById("validationTableBody");
  const closeModalBtn = document.getElementById("closeModalBtn");
  const bypassBtn = document.getElementById("bypassBtn"); // Get the bypass button

  closeModalBtn.addEventListener("click", () => modal.classList.add("hidden"));
  modal.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
  });

  // Bypass Button Logic
  bypassBtn.addEventListener("click", async () => {
    modal.classList.add("hidden");
    // Re-submit Step 2 with the skip flag
    await submitAndDownload({
      ...step2Config, // Spread the config used for Step 2
      additionalData: { skip_validation: "true" },
    });
  });

  function showValidationErrorModal(errorText) {
    tableBody.innerHTML = "";
    // Clean text: strip "Processing Failed" and split lines
    const cleanText = errorText.replace(/Processing Failed.*?:/gi, "").trim();
    const lines = cleanText.split("\n");

    lines.forEach((line) => {
      if (line.trim() === "") return;
      const tr = document.createElement("tr");
      tr.className = "border-b border-gray-100 last:border-0";
      tr.innerHTML = `
        <td class="py-3 px-2 align-top w-10">
            <svg class="w-6 h-6 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        </td>
        <td class="py-3 px-2 text-gray-700 font-medium">${line.trim()}</td>`;
      tableBody.appendChild(tr);
    });
    modal.classList.remove("hidden");
  }

  // ----- Shared Download Helper -----
  async function submitAndDownload({
    form,
    endpoint,
    submitBtn,
    statusDiv,
    filenameBuilder,
    additionalData = {}, // New parameter for extra flags
  }) {
    statusDiv.classList.add("hidden");
    submitBtn.disabled = true;
    const originalBtnText = submitBtn.textContent;
    submitBtn.textContent = "Processing...";

    try {
      const formData = new FormData(form);

      // Append any additional data (like the bypass flag)
      for (const key in additionalData) {
        formData.append(key, additionalData[key]);
      }

      const response = await fetch(endpoint, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();

        // Updated check to trigger modal for validation errors
        if (
          errorText.includes("In rows") ||
          errorText.includes("Writer Total")
        ) {
          showValidationErrorModal(errorText);
          statusDiv.classList.add("hidden");
        } else {
          statusDiv.classList.remove("hidden");
          statusDiv.classList.add("bg-red-100", "text-red-800");
          statusDiv.textContent = `Error: ${errorText}`;
        }
        return;
      }

      // Handle Success
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filenameBuilder();
      document.body.appendChild(a);
      a.click();
      a.remove();

      statusDiv.classList.remove("hidden");
      statusDiv.className =
        "status-message mt-6 p-4 rounded-md bg-green-100 text-green-800";
      statusDiv.textContent = "Success! File downloaded.";
    } catch (error) {
      statusDiv.classList.remove("hidden");
      statusDiv.textContent = `Unexpected error: ${error.message}`;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalBtnText;
    }
  }

  // ----- Form Listeners -----
  const jot1 = document.getElementById("jotform_file_step1");
  document
    .getElementById("uploadFormStep1")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      await submitAndDownload({
        form: e.target,
        endpoint: "/process",
        submitBtn: document.getElementById("submitBtnStep1"),
        statusDiv: document.getElementById("statusStep1"),
        filenameBuilder: () => {
          const base = jot1.files[0]
            ? jot1.files[0].name.split(".").slice(0, -1).join(".")
            : "file";
          return `${base}_curve_ready_step1.xlsx`;
        },
      });
    });

  const curve2 = document.getElementById("curve_file_step2");

  // Define config object so we can reuse it in the bypass button
  const step2Config = {
    form: document.getElementById("uploadFormStep2"),
    endpoint: "/process_step2",
    submitBtn: document.getElementById("submitBtnStep2"),
    statusDiv: document.getElementById("statusStep2"),
    filenameBuilder: () => {
      const base = curve2.files[0]
        ? curve2.files[0].name.split(".").slice(0, -1).join(".")
        : "file";
      return `${base}_curve_ready_step2.xlsx`;
    },
  };

  document
    .getElementById("uploadFormStep2")
    .addEventListener("submit", async (e) => {
      e.preventDefault();
      await submitAndDownload(step2Config);
    });
});
