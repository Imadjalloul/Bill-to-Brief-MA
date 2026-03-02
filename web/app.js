async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`);
  }
  return response.json();
}

function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function renderList(target, items) {
  target.innerHTML = "";
  const template = document.getElementById("itemTemplate");

  if (!items.length) {
    target.innerHTML = "<li class='card'>No records found.</li>";
    return;
  }

  for (const item of items) {
    const node = template.content.cloneNode(true);
    const link = node.querySelector(".title");
    const summary = node.querySelector(".summary");
    const meta = node.querySelector(".meta");

    link.textContent = item.title || `Record ${item.id}`;
    link.href = item.url || "#";
    summary.textContent = item.summary || "No summary available.";
    meta.textContent = `Source: ${item.source || "unknown"} • Published: ${formatDate(item.published_at)}`;

    target.appendChild(node);
  }
}

async function refresh() {
  const [bills, updates] = await Promise.all([
    loadJson("/data/bills.json"),
    loadJson("/data/updates.json"),
  ]);

  document.getElementById("recordCount").textContent = String(bills.count ?? 0);
  document.getElementById("generatedAt").textContent = formatDate(bills.generated_at);

  renderList(document.getElementById("billsList"), bills.records || []);
  renderList(document.getElementById("updatesList"), updates.records || []);
}

async function bootstrap() {
  const refreshBtn = document.getElementById("refreshBtn");
  refreshBtn.addEventListener("click", () => {
    refresh().catch((error) => {
      alert(error.message);
    });
  });

  try {
    await refresh();
  } catch (error) {
    document.getElementById("billsList").innerHTML = `<li class='card'>${error.message}</li>`;
  }
}

bootstrap();
