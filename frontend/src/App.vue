<script setup>
import { RouterView, RouterLink } from 'vue-router'
</script>

<template>
  <div id="app">
    <header class="app-header">

      <!-- Barra di navigazione -->
      <nav class="navbar">
        <RouterLink to="/" class="nav-link">Home</RouterLink>
        <RouterLink to="/upload" class="nav-link">Upload</RouterLink>
      </nav>
    </header>
    
    <main>
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

body {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

#app {
  min-height: 100vh;
  padding: 20px;
}

.app-header {
  text-align: center;
  margin-bottom: 20px;
}

.app-header h1 {
  color: white;
  font-size: 2.5rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  margin-bottom: 15px;
}

/* Navbar */
.navbar {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-size: 1.1rem;
  font-weight: bold;
  padding: 8px 14px;
  border-radius: 8px;
  transition: background 0.3s, transform 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.router-link-active {
  background: rgba(255, 255, 255, 0.3);
}
</style>
