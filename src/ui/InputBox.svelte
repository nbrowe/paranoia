<script>
  import Button from "../ui/Button.svelte";

  export let placeholder;

  let text = "";
  let sendDisabled = true;

  const handleInput = () => {
    if (text.trim().length > 0) {
      sendDisabled = false;
    } else {
      sendDisabled = true;
    }
  };

  const handleSubmit = () => {
    if (text.trim().length > 0) {
      // Broadcast contents of message box to server
      // Reset message box for next message
    }
  };
</script>

<form on:submit|preventDefault={handleSubmit}>
  <div class="input-group">
    <input
      type="text"
      bind:value={text}
      on:input={handleInput}
      placeholder={placeholder}
    />
    <Button disabled={sendDisabled} type="submit">➡</Button>
  </div>
</form>

<style>
  .input-group {
    display: flex;
    flex-direction: row;
    border: 1px solid #ccc;
    padding: 8px 10px;
    border-radius: 8px;
    margin-top: 15px;
  }

  input {
    flex-grow: 2;
    border: none;
    font-size: 16px;
  }

  input:focus {
    outline: none;
  }
</style>
