<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div id="app">
    <header class="topbar">
      <RouterLink to="/" class="nav-link">Home</RouterLink>
      <RouterLink to="/upload" class="nav-link">Upload</RouterLink>
    </header>

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  font-family: system-ui, sans-serif;
  background: #343541; 
  color: #fff;
}

/* Topbar */
.topbar {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #202123;
  padding: 6px 12px;   
  height: 40px;        
  border-bottom: 1px solid #2a2b32;
}

.nav-link {
  color: #fff;
  text-decoration: none;
  font-size: 0.9rem;   
  padding: 4px 8px;
  border-radius: 4px;
}

.router-link-active {
  background: #343541;
}

/* Main content */
.main-content {
  flex: 1;
  overflow-y: auto;
}
</style>

