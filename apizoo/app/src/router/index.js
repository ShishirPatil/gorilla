import { createRouter, createWebHistory } from 'vue-router';
import ApiZoo from '../components/ApiZoo.vue';
import ApiDetail from '../components/ApiDetail.vue';

const routes = [
  {
    path: '/',
    name: 'ApiZoo',
    component: ApiZoo,
  },
  {
    path: '/api/:apiName',
    name: 'apiDetail',
    component: ApiDetail,
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;