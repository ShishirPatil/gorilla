<template>
  <div>
    <div class="navbar">
      <a href="../../index.html">Home</a>
      <span class="nav-separator">|</span>
      <a href="../../blog.html">Blog</a>
      <span class="nav-separator">|</span>
      <a href="../">API Zoo Index</a>
  </div>
  <div class="api-detail-container">
  <v-container class="pa-6">
    <v-card class="ma-5 elevation-2">
      <v-card-title class="headline">
        <v-row no-gutters align="center" justify="space-between">
          <v-col cols="11">{{ apiDetails.api_name }}</v-col>
          <v-col cols="1" class="text-right">
            <a :href="apiDetails.file_url" target="_blank">
              <v-icon large>mdi-github</v-icon>
            </a>
          </v-col>
        </v-row>
      </v-card-title>
      <v-card-subtitle class="grey--text">Version: {{ apiDetails.api_version }}</v-card-subtitle>
      <v-card-text>
        <v-divider></v-divider>
        <div class="my-6">
          <h3>Functionality</h3>
          <p class="functionality-text">{{ apiDetails.functionality }}</p>
        </div>
        <div class="my-6">
          <h3>API Call</h3>
          <div class="api-call-wrapper">
            <code class="api-call">{{ apiDetails.api_call }}</code>
          </div>
        </div>
        <div class="my-6">
          <h3>API Arguments</h3>
          <v-list dense>
            <v-list-item v-for="(value, name) in apiDetails.api_arguments" :key="name">
              <v-list-item-content>
                <v-list-item-title>{{ name }}: {{ value }}</v-list-item-title>
              </v-list-item-content>
            </v-list-item>
          </v-list>
        </div>
        <div class="my-6">
          <h3>Example Code</h3>
          <div class="code-container" style="overflow-x: auto;">
            <pre class="language-python"><code>{{ apiDetails.example_code }}</code></pre>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
  </div>
  </div>
</template>
  
<script>
export default {
  computed: {
    apiDetails() {
      return this.$store.getters.getApiDetails;
    },
  },
};
</script>

<style scoped>
.navbar {
  position: absolute;
  top: 0;
  right: 20px;
  padding: 10px;
  z-index: 100;
  font-size: 18px;
  font-family: 'Source Sans Pro', sans-serif;
}

.navbar a {
  color: #007bff;
  text-decoration: none;
}

.navbar a:hover {
  color: #055ada;
  text-decoration: underline;
}

.nav-separator {
  margin: 0 8px;
  color: #000;
}

.api-detail-container {
  font-family: 'Source Sans Pro', sans-serif;
  max-width: 1080px;
  margin: auto;
  padding: 20px;
  padding-top: 50px;
}
.headline {
  margin-top: 16px;
  font-size: 24px;
  font-weight: bold;
}
.grey--text {
  color: #5f5f5f;
  font-size: 16px;
}
.code-container pre {
  margin-top: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.functionality-text {
  margin-top: 12px;
  font-size: 16px;
}

.api-call-container {
  margin-top: 12px;
  font-size: 16px;
}

.api-call-wrapper {
  margin-top: 12px;
  overflow-x: auto;
  background-image: linear-gradient(to right, #94caff, #3197fd);
  padding: 8px 16px;
  border-radius: 20px;
  white-space: nowrap;
}

.api-call {
  color: #000000;
  font-family: 'Source Sans Pro', monospace;
  font-size: 16px;
}


</style>