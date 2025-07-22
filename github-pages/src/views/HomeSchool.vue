<template>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <div style="flex: 1;">
        <a href="/">
          <img :src="ucmLogo" height="60" alt="UC Merced Logo" />
        </a>
      </div>

      <!--  Mobile ID logo  -->
      <div class="col-xs-8 text-center">
        <img :src="mobileIdLogo" height="60" alt="Mobile ID" />
      </div>
      <div style="flex: 1;"></div>
    </div>

    <div style="border-top: 1px solid white; margin: 0 20px;"></div>

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
      
      <!-- User ID (student-id) -->
      <h4
        id="student-id"
        class="white-h4"
        style="color:white !important;display:none;"
      >
        {{ profile.information_id }}
      </h4>

      <!-- Button -->
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
      <!-- Barcode canvas -->
      <div id="qrcode-div" style="display:none;">
        <canvas ref="barcodeCanvas" class="pdf417"></canvas>
      </div>
      
      <!-- Progress bar -->
      <div id="qrcode-code" style="display:none;margin-top: 20px;">
        <div class="progress">
          <div
            class="progress-bar progress-bar-white"
            role="progressbar"
            style="width: 100%; transition: none;"
            ref="progressBar"
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
import {computed, nextTick, onMounted, ref} from "vue";
import {userInfo} from "@/api/auth";

import ucmLogo from "@/assets/images/ucm3.png";
import mobileIdLogo from "@/assets/images/mobileid_logo.png";

/* ── reactive state ─────────────────────────────────────────────────────── */
const profile = ref({name: "", information_id: "", user_profile_img: ""});
const loading = ref(false);
const serverStatus = ref("Emergency");
const barcodeCanvas = ref(null);
const progressBar = ref(null);
let resetTimer = null;

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
function getCookie(name) {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : "";
}

async function apiGenerateBarcode() {
  const res = await fetch("http://127.0.0.1:8000/generate_barcode/", {
    method: "POST",
    credentials: "include",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json"
    }
  });
  if (!res.ok) throw new Error(`Barcode generation failed: ${res.status}`);
  const data = await res.json();
  console.log("API Response:", data);
  return data;
}

/* ── Main handler exactly like original JS code ─────────────────────────── */
async function handleGenerate() {
  loading.value = true;
  serverStatus.value = "Processing";

  console.log("=== Starting barcode generation ===");
  console.log("jQuery available:", typeof window.$);
  console.log("PDF417 available:", typeof window.PDF417);

  try {
    console.log("Calling API...");
    const {status, message, barcode} = await apiGenerateBarcode();
    console.log("API Response received:", {status, message, barcode});
    
    serverStatus.value = message || "Success";

    if (status === "success" && barcode) {
      console.log("API returned barcode data:", barcode);

      // Generate barcode using API response data
      await nextTick();
      console.log("About to draw PDF417...");
      drawPdf417(barcode);

      // Animation logic exactly like original
      console.log("Starting animation logic...");
      
      // Check if jQuery is available
      if (typeof window.$ === 'undefined') {
        console.error("jQuery is not available!");
        return;
      }

      const $button = window.$('#show-info-button');
      const $studentId = window.$('#student-id');
      const $qrcodeCode = window.$('#qrcode-code');
      const $qrcodeDiv = window.$('#qrcode-div');

      console.log("jQuery elements found:", {
        button: $button.length,
        studentId: $studentId.length,
        qrcodeCode: $qrcodeCode.length,
        qrcodeDiv: $qrcodeDiv.length
      });

      const isFaded = $button.css('display') === 'none';
      console.log("Button is faded:", isFaded);

      if (isFaded) {
        // Reset state - exactly like original
        setTimeout(() => {
          $button.fadeIn();
        }, 400);
        $studentId.fadeOut();
        $qrcodeCode.fadeOut();
        $qrcodeDiv.fadeOut();
      } else {
        // Show barcode sequence - exactly like original
        console.log("Starting show sequence...");
        $button.fadeOut();

        setTimeout(() => {
          console.log("Showing elements...");
          $qrcodeDiv.fadeIn();
          $qrcodeCode.fadeIn();
          $studentId.fadeIn();

          // Progress bar animation exactly like original
          const $progressBar = window.$('.progress-bar');
          console.log("Progress bar found:", $progressBar.length);
          
          $progressBar.css({
            "transition": "none",
            "width": "100%"
          });
          console.log("Set progress bar to 100%");

          // Short delay before applying transition again for smooth animation
          setTimeout(() => {
            $progressBar.css({
              "transition": "width 10s linear",
              "width": "0%"
            });
            console.log("Started 10s animation to 0%");
          }, 50);

        }, 400);

        // Hide barcode after 10.4 seconds - exactly like original
        clearTimeout(resetTimer);
        resetTimer = setTimeout(() => {
          $qrcodeDiv.fadeOut(400);
          $qrcodeCode.fadeOut(400);
          $studentId.fadeOut(400);
          setTimeout(() => {
            $button.fadeIn();
          }, 400);
        }, 10400);
      }
    }
  } catch (err) {
    serverStatus.value = "Error";
    console.error("Barcode generation error:", err);
  } finally {
    loading.value = false;
  }
}

/* ── barcode renderer using API response data ──────────────────────────────── */
function drawPdf417(barcodeData) {
  const canvas = barcodeCanvas.value;
  if (!canvas) {
    console.error("Canvas element not found");
    return;
  }

  console.log("Generating PDF417 barcode for data:", barcodeData);

  // Check if global PDF417 object is available
  if (typeof window.PDF417 === 'undefined') {
    console.error("PDF417 library not loaded");
    return;
  }

  try {
    // Initialize PDF417 with the barcode data from API
    window.PDF417.init(barcodeData);
    const barcode = window.PDF417.getBarcodeArray();

    if (!barcode || !barcode.bcode || barcode.num_rows <= 0) {
      console.error("Failed to generate PDF417 barcode array");
      return;
    }

    console.log("Barcode array generated:", {
      rows: barcode.num_rows,
      cols: barcode.num_cols
    });

    // Block sizes exactly like original
    const bw = 2.5;
    const bh = 1;

    // Create canvas exactly like original
    const container = document.getElementById('qrcode-div');
    if (container.firstChild && container.firstChild.tagName === 'CANVAS') {
      container.removeChild(container.firstChild);
    }

    canvas.setAttribute("id", "canvas");
    canvas.width = bw * barcode.num_cols;
    canvas.height = bh * barcode.num_rows;

    const ctx = canvas.getContext('2d');

    // Graph barcode elements exactly like original
    let y = 0;
    for (let r = 0; r < barcode.num_rows; r++) {
      let x = 0;
      for (let c = 0; c < barcode.num_cols; c++) {
        if (barcode.bcode[r][c] == 1) {
          ctx.fillStyle = '#000000';
          ctx.fillRect(x, y, bw, bh);
        } else {
          ctx.fillStyle = '#FFFFFF';
          ctx.fillRect(x, y, bw, bh);
        }
        x += bw;
      }
      y += bh;
    }

    console.log("PDF417 barcode rendered successfully");

  } catch (error) {
    console.error("PDF417 generation failed:", error);
  }
}
</script>

<!-- ────────── GLOBAL STYLES (order matters) ────────── -->
<style src="bootstrap/dist/css/bootstrap.min.css"></style>
<style src="@fortawesome/fontawesome-free/css/all.min.css"></style>
<style src="@/assets/css/mobileid.css"></style>

<!-- ────────── PAGE-SPECIFIC MINIMAL OVERRIDES ────────── -->
<style scoped>
/* Header styles */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5em;
}

.header > div {
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf417 {
  background: #fff;
  image-rendering: pixelated;
  border: 1px solid #dee2e6;
  max-width: 100%;
  height: auto;
  margin: 10px auto;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  display: block;
}

.progress {
  margin-top: 15px;
  width: 100%;
  height: 8px;
  background-color: rgba(255,255,255,0.3);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar-white {
  background-color: #ffc107;
  height: 100%;
  position: absolute;
  left: 0;
  top: 0;
}

/* Button hover effect */
#show-info-button:hover {
  transform: translateY(-2px);
  transition: transform 0.2s ease;
}
</style>