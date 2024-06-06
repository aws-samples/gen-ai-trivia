import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import TriviaGame from '../views/TriviaGame.vue'
import FinalScore from '../components/FinalScore.vue'


const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home
    },
    {
        path: '/trivia-game/:topic',
        name: 'Trivia Game',
        component: TriviaGame,
        props: true
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router