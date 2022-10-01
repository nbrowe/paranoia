<script>
	import FeedbackList from './components/FeedbackList.svelte';

	let feedback = [
		{
			id: 1,
			rating: 10,
			text: 'I cumulus in my pumulus...',
		},
		{
			id: 2,
			rating: 9,
			text: 'He she it we me meee.',
		},
		{
			id: 3,
			rating: 7,
			text: 'GOOD LORD EVERYTHING IS ON FIRE !',
		}
	]

	const deleteFeedback = (e) => {
		const itemId = e.detail;
		feedback = feedback.filter((item) => item.id != itemId);
	}
</script>

<main class="container">
	<FeedbackList {feedback}  on:delete-feedback={deleteFeedback} />
</main>