async function printAnalysis() {
  const fileInput = document.getElementById("diffFile");
  const mode = document.getElementById("mode").value;
  const output = document.getElementById("analysis-output");
  const printer = document.getElementById("printer");
  const status = document.getElementById("statusText");

  resetLEDs();
  printer.classList.remove("printing");

  if (!fileInput.files.length) {
    status.textContent = "Insert paper (upload a diff).";
    return;
  }

  status.textContent = "Printer warming up…";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);
  formData.append("mode", mode);

  try {
    const res = await fetch("/analyze", {
      method: "POST",
      body: formData
    });

    const data = await res.json();

    // ✅ Set full analysis text
    output.textContent = data.analysis;

    // Trigger animation + LED after a short delay
    setTimeout(() => {
      status.textContent = "Printing…";
      printer.classList.add("printing");
      setRiskLED(data.risk);
    }, 300);

  } catch (err) {
    status.textContent = "Printer error.";
    console.error(err);
  }
}

function resetLEDs() {
  document.querySelectorAll(".led").forEach(l => l.classList.remove("on"));
}

function setRiskLED(risk) {
  if (!risk) return;

  if (risk === "high") {
    document.getElementById("led-high").classList.add("on");
  } else if (risk === "medium") {
    document.getElementById("led-medium").classList.add("on");
  } else {
    document.getElementById("led-low").classList.add("on");
  }
}
