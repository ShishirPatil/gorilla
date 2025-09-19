<template>
  <div>
  <div class="navbar">
      <a href="../index.html">Home</a>
      <span class="nav-separator">|</span>
      <a href="../blog.html">Blog</a>
      <span class="nav-separator">|</span>
      <a href="../leaderboard.html">Leaderboard</a>
      <span class="nav-separator">|</span>
      <a href="apizoo/">API Zoo Index</a>
      <span class="nav-separator">|</span>
      <a href="../addapi/">Add Your API</a>
  </div>
  <div class="api-zoo-container">
    <h1>🦍 Gorilla: API Zoo Index 🚀</h1>
    <p>Welcome to the API Zoo, a community-maintained repository of up-to-date API documentation. Our goal is to create and maintain an accessible collection of API documentation that can be utilized by LLMs to extend their capability to use tools through API calls.</p>
    <br>
    <p>If you're interested in contributing to the growth and maintenance of the API Zoo, we encourage you to visit our <a href="https://github.com/ShishirPatil/gorilla/tree/main" target="_blank">GitHub repository</a>. Your contributions can help ensure that the documentation remains current and that new and useful APIs are continually added to our collection. To learn more about how you can contribute, please <a href="https://github.com/ShishirPatil/gorilla/tree/main/data" target="_blank">go here</a>.</p>
    <br>
    <v-text-field
      v-model="search"
      label="Search by api name, contributor, version, or functionality..."
      single-line
      hide-details
    ></v-text-field>
    <v-data-table
      :headers="headers"
      :items="apis"
      :search="search"
      item-key="api_name"
      class="api-data-table"
    >
      <template v-slot:[`item.api_name`]="{ item }">
        <a :href="item.file_url" target="_blank">{{ item.api_name }}</a>
      </template>
      <template v-slot:[`item.action`]="{ item }">
        <v-btn color="primary" @click.stop="() => goToApiDetail(item)">Details</v-btn>
      </template>
    </v-data-table>
  </div>
  </div>
</template>

<script>
export default {
  data: () => ({
    search: '',
    headers: [
      { title: 'API Name', align: 'start', value: 'api_name' },
      { title: 'Contributor', value: 'user_name' },
      { title: 'API Version', align: 'start', value: 'api_version' },
      { title: 'Functionality', value: 'functionality' },
      { title: 'Actions', value: 'action', sortable: false },
    ],
    apis: [],
  }),
  created() {
    this.fetchApis();
  },
  methods: {
    async fetchApis() {
      try {
        const response = await fetch('https://apizooindex.gorilla-llm.com/api/data');
        if (!response.ok) throw new Error('Failed to fetch');
        const data = await response.json();
        this.apis = data;
      } catch (error) {
        console.error("There was an error fetching the API data:", error);
      }
    },
    goToApiDetail(item) {
      this.$store.dispatch('updateApiDetails', item);
      this.$router.push({ name: 'apiDetail', params: { apiName: item.api_name } });
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

.api-zoo-container {
  font-family: 'Source Sans Pro', sans-serif;
  color: #313437;
  max-width: 1080px;
  margin: auto;
  margin-bottom: 40px;
}

.api-zoo-container h1 {
  text-align: center;
  font-weight: 400;
  font-size: 2.5rem;
  padding-top: 50px;
  padding-bottom: 30px;
}

.api-zoo-container p {
  text-align: justify;
  color: #212529;
}

.api-zoo-container a {
  color: #1E90FF;
}

.api-zoo-container a:hover {
  color: #055ada;
}

.api-data-table {
  background-color: #fff;
  border: 1px solid #e8e8e8;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.v-btn {
  background-color: #296ADD !important;
  color: #fff !important;
}
</style>
