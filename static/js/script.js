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

    // simple active styling
    const active = "bg-blue-600 text-white border-blue-600";
    const inactive = "bg-white text-gray-800 border-gray-300 hover:bg-gray-50";

    tabStep1.className = `px-4 py-2 rounded-lg font-semibold border transition ${isStep1 ? active : inactive}`;
    tabStep2.className = `px-4 py-2 rounded-lg font-semibold border transition ${!isStep1 ? active : inactive}`;
  }

  tabStep1.addEventListener("click", () => setActiveTab(1));
  tabStep2.addEventListener("click", () => setActiveTab(2));
  setActiveTab(1); // default

  // ----- Shared helpers -----
  async function submitAndDownload({
    form,
    endpoint,
    submitBtn,
    statusDiv,
    filenameBuilder,
  }) {
    statusDiv.classList.add("hidden");
    statusDiv.textContent = "";

    submitBtn.disabled = true;
    const originalBtnText = submitBtn.textContent;
    submitBtn.textContent = "Processing... Please wait.";

    const formData = new FormData(form);
    const filename = filenameBuilder();

    try {
      const response = await fetch(endpoint, { method: "POST", body: formData });

      if (!response.ok) {
        const errorText = await response.text();
        statusDiv.classList.remove("hidden");
        statusDiv.classList.add("bg-red-100", "text-red-800");
        statusDiv.classList.remove("bg-green-100", "text-green-800");
        statusDiv.textContent = `Error: ${errorText}`;
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);

      statusDiv.classList.remove("hidden");
      statusDiv.classList.add("bg-green-100", "text-green-800");
      statusDiv.classList.remove("bg-red-100", "text-red-800");
      statusDiv.textContent = `Success! File "${filename}" has been downloaded.`;
    } catch (error) {
      statusDiv.classList.remove("hidden");
      statusDiv.classList.add("bg-red-100", "text-red-800");
      statusDiv.classList.remove("bg-green-100", "text-green-800");
      statusDiv.textContent = `An unexpected error occurred: ${error.message}`;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = originalBtnText;
    }
  }

  // ----- Step 1 -----
  const formStep1 = document.getElementById("uploadFormStep1");
  const submitBtnStep1 = document.getElementById("submitBtnStep1");
  const statusStep1 = document.getElementById("statusStep1");
  const jot1 = document.getElementById("jotform_file_step1");

  formStep1.addEventListener("submit", async (e) => {
    e.preventDefault();

    await submitAndDownload({
      form: formStep1,
      endpoint: "/process",
      submitBtn: submitBtnStep1,
      statusDiv: statusStep1,
      filenameBuilder: () => {
        let filename = "processed_file.xlsx";
        if (jot1.files.length > 0) {
          const originalName = jot1.files[0].name;
          const parts = originalName.split(".");
          const ext = parts.length > 1 ? "." + parts.pop() : "";
          const name = parts.join(".");
          filename = `${name}_curve_ready_step1${ext}`;
        }
        return filename;
      },
    });
  });

  // ----- Step 2 -----
  const formStep2 = document.getElementById("uploadFormStep2");
  const submitBtnStep2 = document.getElementById("submitBtnStep2");
  const statusStep2 = document.getElementById("statusStep2");
  const curve2 = document.getElementById("curve_file_step2");

  formStep2.addEventListener("submit", async (e) => {
    e.preventDefault();

    await submitAndDownload({
      form: formStep2,
      endpoint: "/process_step2",
      submitBtn: submitBtnStep2,
      statusDiv: statusStep2,
      filenameBuilder: () => {
        let filename = "curve_ready_step2.xlsx";
        if (curve2.files.length > 0) {
          const originalName = curve2.files[0].name;
          const parts = originalName.split(".");
          const ext = parts.length > 1 ? "." + parts.pop() : ".xlsx";
          const name = parts.join(".");
          filename = `${name}_curve_ready_step2${ext}`;
        }
        return filename;
      },
    });
  });
});
