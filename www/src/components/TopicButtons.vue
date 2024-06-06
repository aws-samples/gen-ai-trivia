<template>
    <button @click="selectCategory(topic)" class="btn btn-outline-secondary ms-2 mb-2">{{ topic }}</button>
</template>

<script>
export default {
    props: ['topic'],
    methods: {
        selectCategory(category) {
            this.$router.push({ name: 'Trivia Game', params: { topic: category } });
        }
    }
}
</script>