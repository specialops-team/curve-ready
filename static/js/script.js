document.addEventListener("DOMContentLoaded", () => {
  const uploadForm = document.getElementById("uploadForm");
  const submitBtn = document.getElementById("submitBtn");
  const statusDiv = document.getElementById("status");
  const jotformFile = document.getElementById("jotform_file");

  uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    // 1. Reset status and disable button
    statusDiv.classList.add("hidden");
    statusDiv.textContent = "";
    submitBtn.disabled = true;
    submitBtn.textContent = "Processing... Please wait.";

    const formData = new FormData(uploadForm);

    // Use the filename from the input field to create a default name
    let filename = "processed_file.xlsx";
    if (jotformFile.files.length > 0) {
      // Get the base filename and extension
      const originalName = jotformFile.files[0].name;
      const parts = originalName.split(".");
      const ext = parts.length > 1 ? "." + parts.pop() : "";
      const name = parts.join(".");
      // Set the expected name for display/fallback
      filename = `${name}_curve_ready_step1${ext}`;
    }

    try {
      // 2. Submit data to Flask endpoint
      const response = await fetch("/process", {
        method: "POST",
        body: formData,
      });

      // 3. Handle errors first
      if (!response.ok) {
        const errorText = await response.text();
        statusDiv.classList.remove("hidden");
        statusDiv.classList.add("bg-red-100", "text-red-800");
        statusDiv.classList.remove("bg-green-100", "text-green-800");
        statusDiv.textContent = `Error: ${errorText}`;
        return;
      }

      // 4. Handle success (File download)
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;

      // This line ensures the browser uses the correct, dynamic filename
      a.download = filename;

      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);

      // 5. Update status
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
      // 6. Re-enable button
      submitBtn.disabled = false;
      submitBtn.textContent = "Proceed to Process File";
    }
  });
});
