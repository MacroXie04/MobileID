<template>
  <div class="container">
    <!-- Header -->
    <div
        style="display: flex; align-items: center; justify-content: space-between; padding: 20px 40px; position: relative;"
    >
      <!-- Left: UC Merced Logo -->
      <div style="flex: 1;">
        <a href="/">
          <img :src="ucmLogo" alt="UC Merced Logo" style="height: 60px;"/>
        </a>
      </div>

      <!-- Center: Mobile ID Logo -->
      <div style="flex: 1; display: flex; justify-content: center;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <img :src="mobileIdLogo" alt="Fingerprint" style="height: 60px;"/>
        </div>
      </div>

      <!-- Right Spacer -->
      <div style="flex: 1;"></div>
    </div>
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
          :disabled="loading || isRefreshingToken"
          @click="handleGenerate"
        >
          <b>{{ 
            isRefreshingToken ? "Refreshing Token..." : 
            loading ? "Processing…" : 
            "PAY / Check-in" 
          }}</b>
        </button>
    </div>
  </div>

      <!-- ─────── BARCODE + PROGRESS ─────── -->
    <div id="qrcode" class="text-center">
      <div id="qrcode-div" style="display:none;">
        <canvas ref="barcodeCanvas" class="pdf417"></canvas>
      </div>
      <div id="qrcode-code" style="display:none;">
        <div class="progress center-block">
          <div
            id="progress-bar"
            class="progress-bar progress-bar-white"
            role="progressbar"
            style="width: 100%;"
          ></div>
        </div>
      </div>
    </div>

  <!-- ─────── 3 × 3 GRID ─────── -->
  <div style="margin:auto;max-width:320px;padding-top: 15px;">
    <div class="grid-container">
      <!-- Row 1 -->
      <a href="/edit_profile/" class="btn-grid"><i class="fa fa-credit-card fa-2x"></i>
        <p>Add Funds</p></a>
      <a href="/barcode_dashboard/" class="btn-grid"><i class="fa fa-money-bill fa-2x"></i>
        <p>Balance</p></a>
      <a id="lost-my-card" href="#" class="btn-grid"><i class="fa fa-id-card fa-2x"></i>
        <p>Lost My Card</p></a>

      <!-- Row 2 -->
      <a id="emergency" href="#" class="btn-grid"><i class="fa fa-exclamation-triangle fa-2x"></i>
        <p>{{ serverStatus }}</p></a>
      <a id="gym" href="#" class="btn-grid"><i class="fa fa-dumbbell fa-2x"></i>
        <p>Gym</p></a>
      <a id="resource" href="#" class="btn-grid"><i class="fa fa-info fa-2x"></i>
        <p>Resources</p></a>

      <!-- Row 3 -->
      <a href="https://alynx.ucmerced.edu/" target="_blank" class="btn-grid"><i class="fa fa-link fa-2x"></i>
        <p>Alynx</p></a>
      <a href="/logout/" class="btn-grid"><i class="fa fa-sign-out-alt fa-2x"></i>
        <p>Log out</p></a>
    </div>
  </div>
</template>

<script setup>
import {computed, nextTick, onMounted, ref} from "vue";
import {useRouter} from "vue-router";
import {userInfo} from "@/api/auth";

import ucmLogo from "@/assets/images/ucm3.png";
import mobileIdLogo from "@/assets/images/mobileid_logo.png";

/* ── reactive state ─────────────────────────────────────────────────────── */
const router = useRouter();
const profile = ref({name: "", information_id: "", user_profile_img: ""});
const loading = ref(false);
const serverStatus = ref("Emergency");
const barcodeReady = ref(false);
const barcodeCanvas = ref(null);
const isRefreshingToken = ref(false);

/* avatar helper (base64 → data-URL) */
const avatarSrc = computed(() =>
    profile.value.user_profile_img
        ? `data:image/png;base64,${profile.value.user_profile_img}`
        : ""
);

/* ── 带有自动refresh的用户信息获取 ──────────────────────────────────────────── */
async function getUserInfoWithAutoRefresh() {
  try {
    return await apiCallWithAutoRefresh("http://127.0.0.1:8000/authn/user_info/", {
      method: "GET"
    });
  } catch (error) {
    // 如果是认证错误，已经在apiCallWithAutoRefresh中处理
    if (error.message.includes("Token")) {
      throw error;
    }
    // 其他错误调用原始userInfo函数作为备用
    console.log("🔄 使用备用方法获取用户信息...");
    return await userInfo();
  }
}

/* ── lifecycle ──────────────────────────────────────────────────────────── */
onMounted(async () => {
  try {
    const data = await getUserInfoWithAutoRefresh();
    if (data?.profile) {
      profile.value = data.profile;
      console.log("✅ 用户信息加载成功");
    } else {
      console.log("⚠️ 未获取到用户信息，可能需要登录");
    }
  } catch (error) {
    console.error("❌ 获取用户信息失败:", error);
    // 如果获取用户信息失败，让路由守卫处理认证检查
    if (!error.message.includes("Token")) {
      console.log("🛡️ 将由路由守卫处理认证检查");
    }
  }
});

/* ── helpers ────────────────────────────────────────────────────────────── */
function getCookie(name) {
  const m = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return m ? decodeURIComponent(m[2]) : "";
}

/* ── 认证状态检查函数 ──────────────────────────────────────────────────────── */
function checkAuthenticationError(data, response) {
  // 检查多种token过期的情况
  const isTokenInvalid = 
    data?.code === "token_not_valid" ||
    data?.detail?.includes("token not valid") ||
    data?.detail?.includes("Token is expired") ||
    data?.detail?.includes("Invalid token") ||
    response?.status === 401 ||
    response?.status === 403;
    
  if (isTokenInvalid) {
    console.log("检测到认证错误:", data);
    return true;
  }
  
  return false;
}

/* ── Token刷新函数 ──────────────────────────────────────────────────────── */
async function refreshToken() {
  // 防止并发刷新
  if (isRefreshingToken.value) {
    console.log("⏳ Token刷新正在进行中，等待完成...");
    // 等待当前刷新完成
    while (isRefreshingToken.value) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return true; // 假设刷新成功，让调用者重试
  }

  isRefreshingToken.value = true;
  
  try {
    console.log("🔄 尝试刷新access token...");
    serverStatus.value = "Refreshing...";
    
    const res = await fetch("http://127.0.0.1:8000/authn/token/refresh/", {
      method: "POST",
      credentials: "include",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json"
      }
    });
    
    const data = await res.json();
    console.log("Token refresh response:", data);
    
    if (res.ok && data) {
      console.log("✅ Token刷新成功");
      serverStatus.value = "Processing";
      return true;
    } else {
      console.log("❌ Token刷新失败:", data);
      serverStatus.value = "Auth Failed";
      return false;
    }
  } catch (error) {
    console.error("❌ Token刷新请求失败:", error);
    serverStatus.value = "Network Error";
    return false;
  } finally {
    isRefreshingToken.value = false;
  }
}

/* ── 带有Token自动刷新的API调用函数 ──────────────────────────────────────────── */
async function apiCallWithAutoRefresh(url, options = {}, retryCount = 0) {
  const maxRetries = 1; // 最多重试1次
  
  try {
    const res = await fetch(url, {
      credentials: "include",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/json",
        ...options.headers
      },
      ...options
    });
    
    const data = await res.json();
    console.log(`API Response from ${url}:`, data);
    
    // 检查是否是认证错误
    if (checkAuthenticationError(data, res)) {
      console.log(`🔑 检测到token过期 (重试次数: ${retryCount}/${maxRetries})`);
      
      if (retryCount < maxRetries) {
        console.log("🔄 尝试刷新token后重试...");
        
        // 尝试刷新token
        const refreshSuccess = await refreshToken();
        
        if (refreshSuccess) {
          console.log("✅ Token刷新成功，重新请求...");
          // 递归调用，增加重试次数
          return await apiCallWithAutoRefresh(url, options, retryCount + 1);
        } else {
          console.log("❌ Token刷新失败，需要重新登录");
          handleTokenExpired();
          throw new Error("Token refresh failed");
        }
      } else {
        console.log("❌ 已达到最大重试次数，需要重新登录");
        handleTokenExpired();
        throw new Error("Max retries exceeded");
      }
    }
    
    if (!res.ok) throw new Error(`API call failed: ${res.status} - ${data?.detail || data?.message || 'Unknown error'}`);
    return data;
    
  } catch (error) {
    if (error.message.includes("Token") || error.message.includes("retries")) {
      throw error; // 重新抛出认证相关错误
    }
    console.error(`❌ API请求失败 (${url}):`, error);
    throw new Error(`Network error: ${error.message}`);
  }
}

async function apiGenerateBarcode() {
  return await apiCallWithAutoRefresh("http://127.0.0.1:8000/generate_barcode/", {
    method: "POST"
  });
}

/* ── Token过期处理函数 ──────────────────────────────────────────────────────── */
function handleTokenExpired() {
  // 防止重复调用和在刷新过程中调用
  if (window.isLoggingOut || isRefreshingToken.value) return;
  window.isLoggingOut = true;
  
  console.log("🚨 处理token过期，清除认证信息...");
  
  // 停止token刷新流程（如果正在进行）
  isRefreshingToken.value = false;
  
  // 清除特定的认证相关cookies
  const authCookies = ['csrftoken', 'sessionid', 'access_token', 'refresh_token'];
  authCookies.forEach(cookieName => {
    document.cookie = `${cookieName}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;`;
    document.cookie = `${cookieName}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;domain=${window.location.hostname};`;
  });
  
  // 清除存储中的认证信息
  const authKeys = ['access_token', 'refresh_token', 'user_info', 'auth_token'];
  authKeys.forEach(key => {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  });
  
  // 重置UI状态
  loading.value = false;
  serverStatus.value = "Login Required";
  
  // 显示提示信息并重定向
  setTimeout(() => {
    alert("登录已过期，请重新登录");
    
    // 使用Vue Router进行重定向（符合前端路由设置）
    try {
      console.log("🔄 正在重定向到登录页面...");
      router.push('/login');
      console.log("✅ 已通过Vue Router重定向到登录页面");
    } catch (error) {
      console.error("❌ Vue Router重定向失败，使用原生重定向:", error);
      // 如果Vue Router失败，使用原生重定向
      window.location.href = "/login";
      console.log("✅ 已通过原生方式重定向到登录页面");
    }
    
    // 重置重复调用标志
    setTimeout(() => {
      window.isLoggingOut = false;
      console.log("🔄 重置登出状态标志");
    }, 1000);
  }, 100);
}



/* ── UI actions with jQuery animations ─────────────────────────────────────── */
async function handleGenerate() {
  loading.value = true;
  serverStatus.value = "Processing";

    try {
    const {status, barcode, message} = await apiGenerateBarcode();
    serverStatus.value = message || "Success";

    if (status === "success" && barcode) {
      // First generate the barcode
      await nextTick();
      drawPdf417(barcode);

      // Check if elements are already visible (matching original logic)
      const isFaded = window.$('#show-info-button').css('display') === 'none';
      
      if (isFaded) {
        setTimeout(() => {
          window.$('#show-info-button').fadeIn();
        }, 400);
        window.$('#information_id').fadeOut();
        window.$('#qrcode-code').fadeOut();
        window.$('#qrcode-div').fadeOut();
      } else {
        window.$('#show-info-button').fadeOut();

        setTimeout(() => {
          window.$('#qrcode-div').fadeIn();
          window.$('#qrcode-code').fadeIn();
          window.$('#information_id').fadeIn();

          // Reset progress bar width instantly (without animation)
          window.$('.progress-bar').css({
            "transition": "none",
            "width": "100%"
          });

          // Short delay before applying transition again for smooth animation
          setTimeout(() => {
            window.$('.progress-bar').css({
              "transition": "width 10s linear",
              "width": "0%"
            });
          }, 50);

        }, 400);

        // Hide barcode after 10.4 seconds
        setTimeout(() => {
          window.$('#qrcode-div').fadeOut(400);
          window.$('#qrcode-code').fadeOut(400);
          window.$('#information_id').fadeOut(400);
          setTimeout(() => {
            window.$('#show-info-button').fadeIn();
            // Reset server status back to Emergency
            serverStatus.value = "Emergency";
          }, 400);
        }, 10400); // 10.4 seconds + fade out time
      }
    }
  } catch (err) {
    // 处理不同类型的错误
    if (err.message.includes("Token refresh failed") || err.message.includes("Max retries exceeded")) {
      console.log("🔑 Token刷新失败或达到重试上限，已重定向到登录页");
      return; // 直接返回，不执行后续操作
    } else if (err.message.includes("Network error")) {
      serverStatus.value = "Network Error";
      console.error("🌐 网络错误:", err.message);
    } else {
      serverStatus.value = "Error";
      console.error("❌ 条码生成错误:", err);
    }
  } finally {
    loading.value = false;
  }
}


/* ── barcode renderer using global PDF417 object ──────────────────────────── */
function drawPdf417(text) {
  const canvas = barcodeCanvas.value;
  if (!canvas) {
    console.error("Canvas element not found");
    return;
  }

  console.log("Generating barcode for text:", text);

  // Check if global PDF417 object is available
  if (typeof window.PDF417 === 'undefined') {
    console.error("PDF417 library not loaded");
    return;
  }

  try {
    // Initialize PDF417 with the barcode text
    window.PDF417.init(text);
    const barcodeArray = window.PDF417.getBarcodeArray();

    if (!barcodeArray || !barcodeArray.bcode || barcodeArray.num_rows <= 0) {
      console.error("Failed to generate PDF417 barcode array");
      return;
    }

    console.log("Barcode array generated:", {
      rows: barcodeArray.num_rows,
      cols: barcodeArray.num_cols
    });

    // Set canvas size based on barcode dimensions (matching backend settings)
    const moduleWidth = 2.5;
    const moduleHeight = 1;

    canvas.width = moduleWidth * barcodeArray.num_cols;
    canvas.height = moduleHeight * barcodeArray.num_rows;

    // Remove the style width/height settings that might cause scaling issues
    canvas.style.width = '';
    canvas.style.height = '';

    const ctx = canvas.getContext("2d");

    // Clear the canvas first with white background
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw the barcode exactly like backend implementation
    let y = 0;
    for (let r = 0; r < barcodeArray.num_rows; r++) {
      let x = 0;
      for (let c = 0; c < barcodeArray.num_cols; c++) {
        if (barcodeArray.bcode[r][c] == 1) {
          ctx.fillStyle = '#000000';
          ctx.fillRect(x, y, moduleWidth, moduleHeight);
        }
        // Don't draw white pixels explicitly since we cleared with white
        x += moduleWidth;
      }
      y += moduleHeight;
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
.pdf417 {
  background: #fff;
  image-rendering: pixelated;
  border: 1 solid #dee2e6;
  max-width: 100%;
  height: auto;
  margin: 10px auto;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: block;
}

.progress-container {
  width: 100%;
  max-width: 300px;
  margin: 15px auto 0;
}

#qrcode-code {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  min-height: 60px;
}

.progress {
  width: 90%;
  height: 8px;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
  margin: 10px auto 0 auto;
}

.progress-bar-white {
  background-color: #ffc107;
  height: 100%;
}

/* 按钮悬停效果 */
#show-info-button:hover {
  transform: translateY(-2px);
  transition: transform 0.3s ease-in-out;
}
</style>