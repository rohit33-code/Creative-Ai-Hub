
let currentAudio = null;

document.querySelectorAll(".play-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const audioId = btn.getAttribute("data-audio");
        const audio = document.getElementById(audioId);

        // Stop any currently playing audio
        if (currentAudio && currentAudio !== audio) {
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }

        // If clicking the same audio → toggle off
        if (audio === currentAudio && !audio.paused) {
            audio.pause();
            audio.currentTime = 0;
            btn.innerHTML = "▶";
            currentAudio = null;
            return;
        }

        // Play new audio
        audio.currentTime = 0;
        audio.play();
        btn.innerHTML = "⏸";

        currentAudio = audio;

        // When audio ends → reset icon
        audio.onended = () => {
            btn.innerHTML = "▶";
            currentAudio = null;
        };
    });
});
