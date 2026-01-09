function StatBox({ participants, cycles, unmatched }) {
  return (
    <>
      <p>Participants: {participants}</p>
      <p>Cycles: {cycles}</p>
      <p>Unmatched: {unmatched}</p>
    </>
  );
}

export default StatBox;
