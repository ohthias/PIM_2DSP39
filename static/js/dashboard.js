document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("search");
  const results = document.getElementById("results");

  if (input) {
    input.addEventListener("input", async () => {
      const q = input.value.trim();
      if (!q) {
        results.innerHTML = "";
        return;
      }

      const res = await fetch(`/buscar_alunos?q=${encodeURIComponent(q)}`);
      const alunos = await res.json();

      results.innerHTML = alunos
        .map(a => `<li>${a.nome} (${a.idade} anos)</li>`)
        .join("");
    });
  }
});
