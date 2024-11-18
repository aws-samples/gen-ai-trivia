<template>
    <table class="table table-dark w-50 mt-3">
        <caption class="caption-top">
            <h2>Top {{ numberOfHighScores }} Scores</h2>
        </caption>
        <thead>
            <tr>
                <th scope="col">Rank</th>
                <th scope="col">Name</th>
                <th scope="col">Score</th>
                <th scope="col">Accuracy</th>
                <th scope="col">Adujsted Score for Accuracy</th>
                <th scope="col">Category</th>
            </tr>
        </thead>
        <tbody class="table-group-divider">
            <!-- <tr v-for="scoreItem in topTenScores"> -->
            <tr v-for="(scoreItem, index) in highScores" :key="scoreItem.id">
                <td>{{ index + 1 }}</td>
                <td>{{ scoreItem.name.S }}</td>
                <td>{{ scoreItem.initialScore ? scoreItem.initialScore.N : 'null' }}</td>
                <td>{{ scoreItem.accuracy ? scoreItem.accuracy.N : 'null' }}%</td>
                <td>{{ scoreItem.score.N }}</td>
                <td>{{ scoreItem.category.S }}</td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import data from '../data.json'
export default {
    props: ['highScores'],
    data() {
        return {
            numberOfHighScores: data.highscores.numberOfHighScores
        }
    }
}
</script>