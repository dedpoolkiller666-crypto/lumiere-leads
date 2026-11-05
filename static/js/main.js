/**
 * Форма заявки: проверка полей → POST /api/lead → модальное окно «Спасибо!».
 * Без перезагрузки страницы, через fetch.
 */
(function () {
  "use strict";

  const form = document.getElementById("lead-form");
  const submitBtn = document.getElementById("submit-btn");
  const statusEl = document.getElementById("form-status");
  const modal = document.getElementById("success-modal");
  document.getElementById("year").textContent = new Date().getFullYear();

  /* ---------- Маска телефона: +7 (900) 000-00-00 ---------- */
  const phone = form.elements.phone;
  phone.addEventListener("input", () => {
    let d = phone.value.replace(/\D/g, "");
    if (!d) { phone.value = ""; return; }
    if (phone.value.trim().startsWith("+") && d[0] !== "7") return; // иностранный номер — не форматируем
    if (d[0] === "8") d = "7" + d.slice(1);
    if (d[0] !== "7") d = "7" + d;
    d = d.slice(0, 11);
    let out = "+7";
    if (d.length > 1) out += " (" + d.slice(1, 4);
    if (d.length >= 4) out += ")";
    if (d.length > 4) out += " " + d.slice(4, 7);
    if (d.length > 7) out += "-" + d.slice(7, 9);
    if (d.length > 9) out += "-" + d.slice(9, 11);
    phone.value = out;
  });

  /* ---------- Правила проверки ---------- */
  const rules = {
    name: (v) => (v.trim().length >= 2 ? "" : "Укажите имя (минимум 2 символа)"),
    phone: (v) => {
      const n = v.replace(/\D/g, "").length;
      return n >= 10 && n <= 15 ? "" : "Введите номер полностью";
    },
    email: (v) => (/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) ? "" : "Введите корректный email"),
    comment: (v) => (v.length <= 1000 ? "" : "Не больше 1000 символов"),
  };

  function setError(name, message) {
    const input = form.elements[name];
    const field = input.closest(".field");
    const errEl = form.querySelector(`[data-error-for="${name}"]`);
    field.classList.toggle("is-invalid", Boolean(message));
    input.setAttribute("aria-invalid", message ? "true" : "false");
    errEl.textContent = message || "";
  }

  function validate() {
    let firstInvalid = null;
    Object.keys(rules).forEach((name) => {
      const msg = rules[name](form.elements[name].value);
      setError(name, msg);
      if (msg && !firstInvalid) firstInvalid = form.elements[name];
    });
    if (firstInvalid) firstInvalid.focus();
    return !firstInvalid;
  }

  // Ошибка исчезает, как только пользователь начинает исправлять поле
  Object.keys(rules).forEach((name) => {
    form.elements[name].addEventListener("input", () => {
      if (form.elements[name].closest(".field").classList.contains("is-invalid")) {
        setError(name, rules[name](form.elements[name].value));
      }
    });
  });

  /* ---------- Модальное окно ---------- */
  let lastFocus = null;
  function openModal() {
    lastFocus = document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = "hidden";
    modal.querySelector(".btn").focus();
  }
  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = "";
    if (lastFocus) lastFocus.focus();
  }
  modal.addEventListener("click", (e) => { if (e.target.closest("[data-close]")) closeModal(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !modal.hidden) closeModal(); });

  /* ---------- Отправка ---------- */
  function setLoading(on) {
    submitBtn.disabled = on;
    submitBtn.classList.toggle("is-loading", on);
    submitBtn.querySelector(".btn__label").textContent = on ? "Отправляем…" : "Отправить";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    statusEl.textContent = "";
    if (!validate()) return;

    const payload = {
      name: form.elements.name.value.trim(),
      phone: form.elements.phone.value.trim(),
      email: form.elements.email.value.trim(),
      comment: form.elements.comment.value.trim(),
    };

    setLoading(true);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20000);

    try {
      const res = await fetch("/api/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok && data.ok) {
        form.reset();
        openModal();
      } else if (res.status === 422 && data.errors) {
        Object.entries(data.errors).forEach(([name, msg]) => form.elements[name] && setError(name, msg));
      } else {
        statusEl.textContent = data.message || "Не удалось отправить заявку. Попробуйте ещё раз.";
      }
    } catch (err) {
      console.error("Ошибка отправки формы:", err);
      statusEl.textContent = "Нет связи с сервером. Проверьте интернет и попробуйте ещё раз.";
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  });
})();
