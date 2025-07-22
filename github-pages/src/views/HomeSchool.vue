<!-- src/views/HomeSchool.vue -->
<template>
  <!-- ───── HEADER ───── -->
  <header class="d-flex align-items-center justify-content-between px-4 py-3">
    <a href="/">
      <img :src="ucmLogo" alt="UC Merced Logo" height="60" />
    </a>
    <img :src="mobileIdLogo" alt="MobileID" height="60" />
    <span />
  </header>

  <hr class="m-0" />

  <!-- ───── PROFILE ───── -->
  <section class="text-center mt-4">
    <img
      :src="profile?.avatar ?? avatarPlaceholder"
      :style="avatarStyle"
      class="img-circle"
      alt="avatar"
    />
    <h4 class="white-h4 mt-2">{{ profile?.name }}</h4>
    <h4 id="information_id" class="white-h4">{{ profile?.informationId }}</h4>

    <div id="show-info-button" class="mt-3">
      <button
        class="btn btn-trans btn-trans-default"
        :disabled="loading"
        @click="handleGenerate"
      >
        <b>{{ loading ? "Processing…" : "PAY / Check‑in" }}</b>
      </button>
    </div>
  </section>

  <!-- ───── BARCODE & PROGRESS ───── -->
  <section id="qrcode" class="text-center">
    <div v-show="barcodeReady">
      <canvas ref="barcodeCanvas" width="0" height="0" class="pdf417" />
    </div>
    <br v-show="barcodeReady" />
    <div v-show="barcodeReady">
      <div class="progress" style="width:70%;display:inline-block;">
        <div
          class="progress-bar progress-bar-white"
          role="progressbar"
          :style="{ width: progressWidth + '%', transition: progressTransition }"
        />
      </div>
    </div>
  </section>

  <!-- ───── 3 × 3 GRID ───── -->
  <div style="margin:auto;max-width:320px">
    <div class="grid-container">
      <RouterLink to="/edit_profile"      class="btn-grid"><i class="fa fa-credit-card      fa-2x" /><p>Add Funds</p></RouterLink>
      <RouterLink to="/barcode_dashboard" class="btn-grid"><i class="fa fa-money-bill      fa-2x" /><p>Balance</p></RouterLink>
      <RouterLink to="/"                  class="btn-grid"><i class="fa fa-id-card        fa-2x" /><p>Lost My Card</p></RouterLink>

      <RouterLink to="/"                  class="btn-grid"><i class="fa fa-exclamation-triangle fa-2x" /><p id="server_status">{{ serverStatus }}</p></RouterLink>
      <RouterLink to="/"                  class="btn-grid"><i class="fa fa-dumbbell       fa-2x" /><p>Gym</p></RouterLink>
      <RouterLink to="/"                  class="btn-grid"><i class="fa fa-info           fa-2x" /><p>Resources</p></RouterLink>

      <RouterLink to="/logout"            class="btn-grid"><i class="fa fa-sign-out-alt   fa-2x" /><p>Log out</p></RouterLink>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { userInfo } from "@/api/auth";
import ucmLogo         from "@/assets/images/ucm3.png";
import mobileIdLogo    from "@/assets/images/mobileid_logo.png";
import avatarPlaceholder from "@/assets/images/avatar_placeholder.png";

/* ───── STATE ───── */
const profile            = ref(null);
const loading            = ref(false);
const serverStatus       = ref("Emergency");
const barcodeReady       = ref(false);
const progressWidth      = ref(100);
const progressTransition = ref("none");
const barcodeCanvas      = ref(null);
let   resetTimer;

/* ───── LIFECYCLE ───── */
onMounted(async () => {
  const data = await userInfo();
  profile.value = data?.profile ?? {};
});

/* ───── HELPERS ───── */
function getCookie(name) {
  return document.cookie
    .split(";")
    .map(c => c.trim())
    .find(c => c.startsWith(name + "="))
    ?.split("=")[1] ?? "";
}

async function apiGenerateBarcode() {
  const res = await fetch("/api/generate-barcode/", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": getCookie("csrftoken") }
  });
  if (!res.ok) throw new Error("Barcode generation failed");
  return res.json();
}

/* ───── MAIN ACTION ───── */
async function handleGenerate() {
  try {
    loading.value = true;
    serverStatus.value = "Processing";

    const { status, barcode, message } = await apiGenerateBarcode();
    serverStatus.value = message || "Success";

    if (status === "success") {
      drawPdf417(barcode);
      await nextTick();
      barcodeReady.value = true;

      /* progress bar: 10 s countdown */
      requestAnimationFrame(() => {
        progressTransition.value = "width 10s linear";
        progressWidth.value = 0;
      });
      clearTimeout(resetTimer);
      resetTimer = setTimeout(resetUi, 10400);
    }
  } catch {
    serverStatus.value = "Error";
  } finally {
    loading.value = false;
  }
}

function resetUi() {
  barcodeReady.value     = false;
  progressTransition.value = "none";
  progressWidth.value    = 100;
  serverStatus.value     = "Emergency";
}

function drawPdf417(text) {
  if (!window.PDF417) return;
  window.PDF417.init(text);
  const b  = window.PDF417.getBarcodeArray();
  const bw = 2.5, bh = 1;
  const ctx = barcodeCanvas.value.getContext("2d");
  barcodeCanvas.value.width  = bw * b.num_cols;
  barcodeCanvas.value.height = bh * b.num_rows;
  ctx.clearRect(0, 0, barcodeCanvas.value.width, barcodeCanvas.value.height);

  for (let r = 0; r < b.num_rows; r++) {
    for (let c = 0; c < b.num_cols; c++) {
      ctx.fillStyle = b.bcode[r][c] ? "#000" : "#fff";
      ctx.fillRect(c * bw, r * bh, bw, bh);
    }
  }
}

/* ───── STYLES ───── */
const avatarStyle = {
  width: "100px",
  height: "100px",
  objectFit: "cover",
  borderRadius: "50%",
  boxShadow: "0 4px 12px rgba(255,255,255,0.4)"
};
</script>

<style scoped>
.pdf417         { image-rendering: pixelated; border: 1px solid #dee2e6; }
.grid-container { display: grid; grid-template-columns: repeat(3,1fr); gap: 14px; margin-top: 20px; }
.btn-grid       { display: flex; flex-direction: column; align-items: center; justify-content: center;
                  padding: 12px 4px; border-radius: 12px; background: rgba(255,255,255,0.1);
                  color: #fff; text-decoration: none; transition: background .2s; }
.btn-grid:hover { background: rgba(255,255,255,0.2); }
.white-h4       { color: #fff; }
.btn-trans      { background: transparent; border: 1px solid #fff; color: #fff; }
.btn-trans-default:hover { background: #fff; color: #000; }
</style>
