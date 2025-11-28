"""
Tests for the EpidemicAgent class and related functionality.
"""
import pytest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import numpy as np
import tempfile
import os
from datetime import datetime

# Import the module we're testing
from src.agents.epidemic_agent import load_processed_data, run_epidemic_agent

# Test data
MOCK_CSV_DATA = """Location_Code,Date,Confirmed,Deaths,Recovered,Active,Has_Diagnosis
1,2023-01-01,10,1,5,4,0
2,2023-01-01,20,2,10,8,1
5,2023-01-01,15,1,8,6,1
8,2023-01-01,25,3,12,10,0
1,2023-01-02,15,1,8,6,1
2,2023-01-02,30,3,15,12,0
5,2023-01-02,20,2,10,8,1
8,2023-01-02,35,4,20,11,0
"""

# Additional test cases
MALFORMED_CSV = """Location_Code,Date,Confirmed,Deaths,Recovered,Active
1,2023-01-01,ten,one,five,four
2,2023-01-01,twenty,two,ten,eight
"""

EMPTY_CSV = """Location_Code,Date,Confirmed,Deaths,Recovered,Active,Has_Diagnosis
"""

class TestLoadProcessedData:
    """Tests for the load_processed_data function."""
    
    @patch('pandas.read_csv')
    def test_load_processed_data_success(self, mock_read_csv):
        """Test successful loading of processed data."""
        # Setup mock
        mock_df = pd.read_csv(pd.compat.StringIO(MOCK_CSV_DATA))
        mock_read_csv.return_value = mock_df
        
        # Execute
        result = load_processed_data()
        
        # Assert
        assert isinstance(result, pd.DataFrame)
        assert not result.empty
        assert 'Location_Code' in result.columns
        assert 'Has_Diagnosis' in result.columns
        mock_read_csv.assert_called_once()
    
    def test_load_processed_data_with_real_file(self):
        ""Test loading data from a real temporary file."""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.csv', delete=False) as temp_file:
            temp_file.write(MOCK_CSV_DATA)
            temp_file_path = temp_file.name
        
        try:
            # Patch the path to use our temporary file
            with patch('src.agents.epidemic_agent.DATA_PATH', temp_file_path):
                result = load_processed_data()
                
                # Assert
                assert isinstance(result, pd.DataFrame)
                assert not result.empty
                assert len(result) == 8  # 8 rows in our test data
                assert set(result['Location_Code'].unique()) == {1, 2, 5, 8}
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    @patch('pandas.read_csv')
    def test_load_processed_data_missing_columns(self, mock_read_csv):
        ""Test handling of missing required columns."""
        # Create a DataFrame missing required columns
        mock_df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        mock_read_csv.return_value = mock_df
        
        # Execute and assert
        with pytest.raises(KeyError):
            load_processed_data()
    
    @patch('pandas.read_csv')
    def test_load_processed_data_with_malformed_data(self, mock_read_csv):
        ""Test handling of malformed data."""
        # Mock read_csv to return malformed data
        mock_read_csv.side_effect = pd.errors.ParserError("Malformed CSV")
        
        # Should not raise, should return fallback data
        result = load_processed_data()
        assert not result.empty
        assert 'Location_Code' in result.columns
    
    @patch('pandas.read_csv')
    def test_load_processed_data_file_not_found(self, mock_read_csv):
        """Test behavior when data file is not found."""
        # Setup mock to raise FileNotFoundError
        mock_read_csv.side_effect = FileNotFoundError("File not found")
        
        # Capture warning
        with pytest.warns(UserWarning, match="Using simulated data"):
            # Execute
            result = load_processed_data()
            
            # Assert fallback behavior
            assert isinstance(result, pd.DataFrame)
            assert not result.empty
            assert 'Location_Code' in result.columns
            assert 'Has_Diagnosis' in result.columns
    
    @patch('pandas.read_csv')
    def test_load_processed_data_permission_error(self, mock_read_csv):
        ""Test handling of permission errors when reading file."""
        mock_read_csv.side_effect = PermissionError("Permission denied")
        
        with pytest.warns(UserWarning):
            result = load_processed_data()
            assert not result.empty

class TestEpidemicAgent:
    """Tests for the EpidemicAgent functionality."""
    
    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_success(self, mock_print, mock_get_analysis, mock_load_data):
        """Test successful execution of the epidemic agent."""
        # Setup mocks
        mock_df = pd.read_csv(pd.compat.StringIO(MOCK_CSV_DATA))
        mock_load_data.return_value = mock_df
        
        mock_analysis = """
        Analysis Report:
        - Location 1: Low risk
        - Location 2: Medium risk
        - Location 5: High risk
        - Location 8: Critical risk
        """
        mock_get_analysis.return_value = mock_analysis
        
        # Execute
        run_epidemic_agent()
        
        # Assert
        mock_load_data.assert_called_once()
        mock_get_analysis.assert_called_once()
        
        # Check that the report header was printed
        assert any("EPIDEMIC ALERT SYSTEM REPORT" in str(call) for call in mock_print.call_args_list)
        # Check that the analysis report was printed
        assert any("Analysis Report" in str(call) for call in mock_print.call_args_list)
    
    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_with_different_data_sizes(self, mock_print, mock_get_analysis, mock_load_data):
        ""Test agent with different sizes of input data."""
        # Test with small dataset
        small_data = MOCK_CSV_DATA.split('\n')[0] + '\n' + '\n'.join(MOCK_CSV_DATA.split('\n')[1:3])
        mock_df = pd.read_csv(pd.compat.StringIO(small_data))
        mock_load_data.return_value = mock_df
        mock_get_analysis.return_value = "Test Analysis"
        
        run_epidemic_agent()
        assert mock_get_analysis.called
        
        # Test with large dataset
        large_data = MOCK_CSV_DATA * 100  # 800 rows
        mock_df = pd.read_csv(pd.compat.StringIO(large_data))
        mock_load_data.return_value = mock_df
        mock_get_analysis.reset_mock()
        
        run_epidemic_agent()
        assert mock_get_analysis.called
    
    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_empty_data(self, mock_print, mock_get_analysis, mock_load_data):
        """Test behavior when no data is available."""
        # Setup mocks
        mock_load_data.return_value = pd.DataFrame()
        mock_get_analysis.return_value = "No data to analyze"
        
        # Execute
        run_epidemic_agent()
        
        # Assert
        mock_load_data.assert_called_once()
        mock_get_analysis.assert_called_once()
        assert any("No data to analyze" in str(call) for call in mock_print.call_args_list)
    
    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_with_invalid_data(self, mock_print, mock_get_analysis, mock_load_data):
        ""Test agent behavior with invalid data types in the dataframe."""
        # Create a DataFrame with invalid data types
        invalid_data = pd.DataFrame({
            'Location_Code': ['invalid', 'data', 'here'],
            'Date': ['not', 'a', 'date'],
            'Confirmed': ['not', 'a', 'number'],
            'Deaths': ['invalid', 'data', 'types'],
            'Recovered': [1, 2, 3],
            'Active': [1, 2, 3],
            'Has_Diagnosis': [0, 1, 0]
        })
        mock_load_data.return_value = invalid_data
        
        # Execute
        run_epidemic_agent()
        
        # Should still complete without raising exceptions
        assert mock_get_analysis.called

    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_api_error(self, mock_print, mock_get_analysis, mock_load_data):
        """Test behavior when the Ollama API call fails."""
        # Setup mocks
        mock_df = pd.read_csv(pd.compat.StringIO(MOCK_CSV_DATA))
        mock_load_data.return_value = mock_df
        mock_get_analysis.side_effect = Exception("API Error")
        
        # Execute
        run_epidemic_agent()
        
        # Assert that error handling code was called
        assert any("Error running epidemic agent" in str(call).lower() 
                 for call in mock_print.call_args_list)
    
    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_performance(self, mock_print, mock_get_analysis, mock_load_data):
        ""Test the performance of the epidemic agent with timing."""
        # Setup mocks
        large_data = MOCK_CSV_DATA * 100  # 800 rows
        mock_df = pd.read_csv(pd.compat.StringIO(large_data))
        mock_load_data.return_value = mock_df
        mock_get_analysis.return_value = "Test Analysis"
        
        import time
        start_time = time.time()
        
        run_epidemic_agent()
        
        execution_time = time.time() - start_time
        print(f"\nExecution time: {execution_time:.2f} seconds")
        
        # Assert that it completes in a reasonable time (adjust threshold as needed)
        assert execution_time < 5.0, "Agent took too long to execute"
    
    @patch('src.agents.epidemic_agent.load_processed_data')
    @patch('src.agents.epidemic_agent.get_ollama_analysis')
    @patch('builtins.print')
    def test_run_epidemic_agent_output_format(self, mock_print, mock_get_analysis, mock_load_data):
        ""Test the format of the agent's output."""
        # Setup mocks
        mock_df = pd.read_csv(pd.compat.StringIO(MOCK_CSV_DATA))
        mock_load_data.return_value = mock_df
        mock_get_analysis.return_value = "Test Analysis Output"
        
        run_epidemic_agent()
        
        # Get all print calls
        print_calls = [str(call) for call in mock_print.call_args_list]
        
        # Check for specific output patterns
        assert any("EPIDEMIC ALERT SYSTEM REPORT" in call for call in print_calls)
        assert any("Test Analysis Output" in call for call in print_calls)
