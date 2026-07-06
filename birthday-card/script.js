(function() {
  'use strict';

  // ===== FLOATERS =====
  const floatersEl = document.getElementById('floaters');
  const floaterEmojis = ['❤️', '✨', '🌟', '💖', '⭐', '💕', '🌸', '🎉'];
  for (let i = 0; i < 25; i++) {
    const f = document.createElement('div');
    f.className = 'floater';
    f.textContent = floaterEmojis[i % floaterEmojis.length];
    f.style.left = Math.random() * 100 + '%';
    f.style.fontSize = (Math.random() * 14 + 12) + 'px';
    f.style.setProperty('--fd', (Math.random() * 8 + 6) + 's');
    f.style.setProperty('--fdelay', (Math.random() * 10 + 2) + 's');
    floatersEl.appendChild(f);
  }

  // ===== CONFETTI =====
  function spawnConfetti(count) {
    const colors = ['#d4af37', '#ff6b9d', '#c9a030', '#ff4757', '#9b59b6', '#48d1cc', '#e056fd', '#ffdd59'];
    for (let i = 0; i < count; i++) {
      const el = document.createElement('div');
      el.className = 'confetti-piece';
      const size = Math.random() * 8 + 5;
      el.style.width = size + 'px';
      el.style.height = size * (Math.random() * 0.6 + 0.5) + 'px';
      el.style.background = colors[Math.floor(Math.random() * colors.length)];
      el.style.left = Math.random() * 100 + '%';
      el.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
      el.style.setProperty('--fall-dur', (Math.random() * 2 + 2) + 's');
      el.style.animationDelay = (Math.random() * 0.8) + 's';
      document.body.appendChild(el);
      requestAnimationFrame(() => el.classList.add('fall'));
      setTimeout(() => { if (el.parentNode) el.parentNode.removeChild(el); }, 5000);
    }
  }

  // ===== BACKGROUND MUSIC (HTML5 Audio) =====
  let audioEl = null;
  let isPlaying = false;

  function initAudio() {
    if (audioEl) return;
    audioEl = new Audio('birthday-music.mp3');
    audioEl.loop = true;
    audioEl.volume = 0.7;
    audioEl.preload = 'auto';
    audioEl.load();
  }

  function playMusic() {
    initAudio();
    if (!audioEl) return;
    audioEl.currentTime = 0;
    audioEl.play().catch(function(e) {
      console.log('Audio play blocked, waiting for user interaction');
    });
    isPlaying = true;
  }

  function stopMusic() {
    if (audioEl) {
      audioEl.pause();
      audioEl.currentTime = 0;
    }
    isPlaying = false;
  }

  // ===== CARD OPEN/CLOSE =====
  const card = document.getElementById('card');
  const container = document.getElementById('cardContainer');
  let isOpen = false;
  let animating = false;

  container.addEventListener('click', function(e) {
    if (animating) return;
    animating = true;

    if (!isOpen) {
      card.classList.add('open');
      isOpen = true;
      if (!isPlaying) { playMusic(); document.getElementById('musicBtn').classList.remove('muted'); }
      setTimeout(() => spawnConfetti(50), 300);
      setTimeout(() => spawnConfetti(35), 800);
      setTimeout(() => spawnConfetti(40), 4000);
      setTimeout(() => animating = false, 1300);
    } else {
      card.classList.remove('open');
      isOpen = false;
      setTimeout(() => animating = false, 1300);
    }
  });

  // ===== MUSIC TOGGLE =====
  const musicBtn = document.getElementById('musicBtn');
  musicBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (isPlaying) { stopMusic(); musicBtn.classList.add('muted'); }
    else { playMusic(); musicBtn.classList.remove('muted'); }
  });

  console.log('🎂 Happy Birthday Angel! 🎂');
})();
