import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PDFAnnotation from '../views/PDFAnnotation.vue'
import TranslationExecution from '../views/TranslationExecution.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: 'OceanPDF - 首页'
    }
  },
  {
    path: '/annotation',
    name: 'PDFAnnotation',
    component: PDFAnnotation,
    meta: {
      title: 'OceanPDF - PDF标注'
    }
  },
  {
    path: '/translation',
    name: 'TranslationExecution',
    component: TranslationExecution,
    meta: {
      title: 'OceanPDF - 翻译执行'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router
