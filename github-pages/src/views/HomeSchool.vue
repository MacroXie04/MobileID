<!-- src/views/HomeSchool.vue -->
<template>
  <div class="container">
    <!-- ────────── HEADER ────────── -->
    <div
      class="row is-flex"
      style="display:flex;align-items:center;justify-content:space-between;padding:0.5em;"
    >
      <!--  UC Merced logo  -->
      <div class="col-xs-2">
        <a href="/">
          <img :src="ucmLogo" height="60" alt="UC Merced Logo" />
        </a>
      </div>

      <!--  Mobile ID logo  -->
      <div class="col-xs-8 text-center">
        <img :src="mobileIdLogo" height="60" alt="Mobile ID" />
      </div>

      <!--  spacer  -->
      <div class="col-xs-2 text-right"></div>
    </div>
    <hr style="margin-top:5px;margin-bottom:5px;" />

    <!-- ─────── PROFILE SECTION ─────── -->
    <div class="text-center" style="margin-top:2em;">
      <a href="/edit_profile/" id="setting-icon">
        <img
          :src="avatarSrc"
          class="img-circle"
          alt="User profile picture"
          style="width:100px;height:100px;object-fit:cover;border-radius:50%;box-shadow:0 4px 12px rgba(255,255,255,.4);transition:transform .3s ease-in-out;"
        />
      </a>

      <h4 class="white-h4" style="margin-top:.5em;color:white !important;">
        {{ profile.name }}
      </h4>
      <h4
        id="information_id"
        class="white-h4"
        style="color:white !important;display:none;"
      >
        {{ profile.information_id }}
      </h4>

      <div id="show-info-button" style="margin-top:1em;">
        <button
          class="btn btn-trans btn-trans-default"
          :disabled="loading"
          @click="handleGenerate"
        >
          <b>{{ loading ? "Processing…" : "PAY / Check-in" }}</b>
        </button>
      </div>
    </div>

    <!-- ─────── BARCODE + PROGRESS ─────── -->
    <div id="qrcode" class="text-center">
      <div v-show="barcodeReady" id="qrcode-div">
        <canvas ref="barcodeCanvas" class="pdf417"></canvas>
      </div>
      <br v-show="barcodeReady" />
      <div v-show="barcodeReady" id="qrcode-code" style="height:10%;">
        <div class="progress center-block">
          <div
            class="progress-bar progress-bar-white"
            role="progressbar"
            :style="{ width: progressWidth + '%', transition: progressTransition }"
          ></div>
        </div>
      </div>
    </div>

    <!-- ─────── 3 × 3 GRID ─────── -->
    <div style="margin:auto;max-width:320px;">
      <div class="grid-container">
        <!-- Row 1 -->
        <a href="/edit_profile/"      class="btn-grid"><i class="fa fa-credit-card fa-2x"></i><p>Add Funds</p></a>
        <a href="/barcode_dashboard/" class="btn-grid"><i class="fa fa-money-bill fa-2x"></i><p>Balance</p></a>
        <a id="lost-my-card" href="#" class="btn-grid"><i class="fa fa-id-card fa-2x"></i><p>Lost My Card</p></a>

        <!-- Row 2 -->
        <a id="emergency" href="#" class="btn-grid"><i class="fa fa-exclamation-triangle fa-2x"></i><p>{{ serverStatus }}</p></a>
        <a id="gym"       href="#" class="btn-grid"><i class="fa fa-dumbbell fa-2x"></i><p>Gym</p></a>
        <a id="resource"  href="#" class="btn-grid"><i class="fa fa-info fa-2x"></i><p>Resources</p></a>

        <!-- Row 3 -->
        <a href="https://alynx.ucmerced.edu/"  target="_blank" class="btn-grid"><i class="fa fa-link fa-2x"></i><p>Alynx</p></a>
        <a href="/logout/"                     class="btn-grid"><i class="fa fa-sign-out-alt fa-2x"></i><p>Log out</p></a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from "vue";
import { userInfo } from "@/api/auth";
import { PDF417 } from "@makard/pdf417";

import ucmLogo      from "@/assets/images/ucm3.png";
import mobileIdLogo from "@/assets/images/mobileid_logo.png";

/* ── reactive state ─────────────────────────────────────────────────────── */
const profile            = ref({ name: "", information_id: "", user_profile_img: "" });
const loading            = ref(false);
const serverStatus       = ref("Emergency");
const barcodeReady       = ref(false);
const progressWidth      = ref(100);
const progressTransition = ref("none");
const barcodeCanvas      = ref(null);
let   resetTimer         = null;

/* avatar helper (base64 → data-URL) */
const avatarSrc = computed(() =>
  profile.value.user_profile_img
    ? `data:image/png;base64,${profile.value.user_profile_img}`
    : ""
);

/* ── lifecycle ──────────────────────────────────────────────────────────── */
onMounted(async () => {
  const data = await userInfo();
  if (data?.profile) profile.value = data.profile;
});

/* ── helpers ────────────────────────────────────────────────────────────── */
function getCookie (name) {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : "";
}

async function apiGenerateBarcode () {
  const res = await fetch("http://127.0.0.1:8000/generate_barcode/", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRFToken": getCookie("csrftoken") }
  });
  if (!res.ok) throw new Error("Barcode generation failed");
  return res.json();
}

/* ── UI actions ─────────────────────────────────────────────────────────── */
async function handleGenerate () {
  loading.value      = true;
  serverStatus.value = "Processing";

  try {
    const { status, barcode, message } = await apiGenerateBarcode();
    serverStatus.value = message || "Success";

    if (status === "success") {
      barcodeReady.value = true;
      await nextTick();

      drawPdf417(barcode);

      requestAnimationFrame(() => {
        progressTransition.value = "width 10s linear";
        progressWidth.value      = 0;
      });
      clearTimeout(resetTimer);
      resetTimer = setTimeout(resetUi, 10400);
    }
  } catch (err) {
    serverStatus.value = "Error";
    console.error(err);
  } finally {
    loading.value = false;
  }
}


function resetUi () {
  barcodeReady.value       = false;
  progressTransition.value = "none";
  progressWidth.value      = 100;
  serverStatus.value       = "Emergency";
}

/* ── barcode renderer (hi-DPI-safe) ─────────────────────────────────────── */
function drawPdf417 (text) {
  PDF417.init(text, 2, 0);          // ECC level 2, auto-columns
  const b = PDF417.getBarcodeArray();

  const W = 2;                      // module width  (device-px)
  const H = W * 3;                  // module height ≈ 3:1
  const canvas = barcodeCanvas.value;
  canvas.width  = b.num_cols * W;
  canvas.height = b.num_rows * H;

  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#000";
  for (let r = 0; r < b.num_rows; ++r)
    for (let c = 0; c < b.num_cols; ++c)
      if (b.bcode[r][c])
        ctx.fillRect(c * W, r * H, W, H);

  canvas.style.width  = `${canvas.width  / window.devicePixelRatio}px`;
  canvas.style.height = `${canvas.height / window.devicePixelRatio}px`;
}
</script>

<!-- ────────── GLOBAL STYLES (order matters) ────────── -->
<style src="bootstrap/dist/css/bootstrap.min.css"></style>
<style src="@fortawesome/fontawesome-free/css/all.min.css"></style>
<style src="@/assets/css/mobileid.css"></style>

<!-- ────────── PAGE-SPECIFIC MINIMAL OVERRIDES ────────── -->
<style scoped>
.pdf417 {
  background:#fff;
  image-rendering:pixelated;
  border:1px solid #dee2e6;
  max-width:100%;
  height:auto;
}
</style>
