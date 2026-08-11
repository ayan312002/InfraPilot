function typewriterCycle(element, texts, options = {}) {
  const {
    typeSpeed = 60,
    pauseDuration = 2500,
    eraseSpeed = 40,
    delay = 2500,
  } = options;

  let textIndex = 0;
  let charIndex = 0;
  let isDeleting = false;
  let isPaused = false;
  let timeoutId = null;

  function cycle() {
    if (isPaused) return;

    const currentText = texts[textIndex];

    if (isDeleting) {
      charIndex = Math.max(0, charIndex - 1);
      if (charIndex === 0) {
        isDeleting = false;
        textIndex = (textIndex + 1) % texts.length;
        timeoutId = setTimeout(cycle, delay);
        return;
      }
    } else {
      if (charIndex < currentText.length) {
        charIndex++;
      } else {
        timeoutId = setTimeout(() => {
          isDeleting = true;
          cycle();
        }, pauseDuration);
        return;
      }
    }

    element.textContent = currentText.substring(0, charIndex);
    element.style.borderRight = charIndex > 0 ? "2px solid #3b82f6" : "none";

    timeoutId = setTimeout(
      cycle,
      isDeleting ? eraseSpeed : typeSpeed
    );
  }

  timeoutId = setTimeout(cycle, delay);

  return function stop() {
    isPaused = true;
    if (timeoutId) clearTimeout(timeoutId);
  };
}

function shimmer(element) {
  const shimmer = document.createElement("div");
  shimmer.className = "shimmer-overlay";
  element.appendChild(shimmer);
  return function stop() {
    shimmer.remove();
  };
}

function fadeIn(element, duration = 600) {
  element.style.opacity = "0";
  element.style.transition = `opacity ${duration}ms ease`;
  element.style.display = "block";
  requestAnimationFrame(() => {
    element.style.opacity = "1";
  });
}

function fadeOut(element, duration = 600) {
  return new Promise((resolve) => {
    element.style.opacity = "0";
    element.style.transition = `opacity ${duration}ms ease`;
    setTimeout(() => {
      element.style.display = "none";
      resolve();
    }, duration);
  });
}

function slideIn(element, direction = "left", duration = 500) {
  element.style.opacity = "0";
  element.style.transform = `translateX(${direction === "left" ? -20 : 20}px)`;
  element.style.transition = `all ${duration}ms cubic-bezier(0.25, 0.46, 0.45, 0.94)`;
  element.style.display = "block";
  requestAnimationFrame(() => {
    element.style.opacity = "1";
    element.style.transform = "translateX(0)";
  });
}

function animateNumber(element, start, end, duration = 2000) {
  let startTs = null;
  const step = (timestamp) => {
    if (!startTs) startTs = timestamp;
    const progress = Math.min((timestamp - startTs) / duration, 1);
    const value = Math.floor(progress * (end - start) + start);
    element.textContent = value + "+";
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function drawCheckmark(element) {
  const svg = element.querySelector("svg");
  if (!svg) return;
  const path = svg.querySelector("path");
  if (!path) return;
  path.style.animation = "none";
  void path.offsetWidth;
  path.style.animation = "drawCheck 0.5s ease-in-out forwards";
}

function spin(element) {
  element.classList.add("spin");
}

function stopSpin(element) {
  element.classList.remove("spin");
  drawCheckmark(element);
}

function createParticleField(container, count = 30) {
  if (!container) return;
  container.innerHTML = "";
  for (let i = 0; i < count; i++) {
    const p = document.createElement("div");
    p.className = "particle";
    const size = Math.random() * 3 + 1;
    p.style.width = `${size}px`;
    p.style.height = `${size}px`;
    p.style.left = `${Math.random() * 100}%`;
    p.style.top = `${Math.random() * 100}%`;
    p.style.opacity = Math.random() * 0.4 + 0.1;
    p.style.animationDuration = `${Math.random() * 15 + 10}s`;
    p.style.animationDelay = `${Math.random() * 5}s`;
    container.appendChild(p);
  }
}

function createOrbs(container, count = 6) {
  if (!container) return;
  container.innerHTML = "";
  for (let i = 0; i < count; i++) {
    const orb = document.createElement("div");
    orb.className = `bg-orb orb-${i + 1}`;
    orb.style.left = `${10 + Math.random() * 80}%`;
    orb.style.top = `${10 + Math.random() * 80}%`;
    orb.style.animationDuration = `${Math.random() * 25 + 20}s`;
    orb.style.animationDelay = `${Math.random() * 5}s`;
    container.appendChild(orb);
  }
}
