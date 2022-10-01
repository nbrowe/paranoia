<script>
  import { FeedbackStore } from "../stores.js";

  // reactive values
  $: count = $FeedbackStore.length;
  $: average =
    $FeedbackStore.reduce((prev, { rating }) => prev + rating, 0) / count;;
</script>

<div class="feedback-stats">
  <h4>{count} Reviews</h4>
  <h4>Ratings Average: {average}</h4>
</div>

<style>
  .feedback-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
</style>
