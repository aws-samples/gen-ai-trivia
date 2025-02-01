<template>
    <table class="table table-dark w-50 mt-3">
        <caption class="caption-top">
            <h2>{{ $t('topScores.top') }} {{ numberOfHighScores }} {{ $t('topScores.scores') }}</h2>
        </caption>
        <thead>
            <tr>
                <th scope="col">{{ $t('topScores.rank') }}</th>
                <th scope="col">{{ $t('topScores.name') }}</th>
                <th scope="col">{{ $t('topScores.score') }}</th>
                <th scope="col">{{ $t('topScores.accuracy') }}</th>
                <th scope="col">{{ $t('topScores.adjusted') }}</th>
                <th scope="col">{{ $t('topScores.category') }}</th>
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