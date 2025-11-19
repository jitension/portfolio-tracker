/**
 * Holdings Table Component
 * Displays holdings in a sortable, filterable DataGrid
 */
import { useEffect, useState, useMemo } from 'react';
import {
  Box,
  Typography,
  Chip,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Paper,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridSortModel } from '@mui/x-data-grid';
import { useAppDispatch, useAppSelector } from '../../../store';
import { fetchHoldings, setFilters } from '../store/holdingsSlice';
import type { Holding } from '../../../types/holdings';

// Format currency
const formatCurrency = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(numValue);
};

// Format percent
const formatPercent = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`;
};

// Get P/L color
const getPLColor = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return numValue >= 0 ? 'success.main' : 'error.main';
};

// Convert value to number
const toNumber = (value: number | string | null | undefined): number => {
  return typeof value === 'string' ? parseFloat(value) : (value || 0);
};

// Custom Footer Component
const CustomFooter = ({ holdings }: { holdings: Holding[] }) => {
  const totals = useMemo(() => {
    return holdings.reduce(
      (acc, holding) => ({
        marketValue: acc.marketValue + toNumber(holding.market_value),
        totalPL: acc.totalPL + toNumber(holding.total_pl),
        dailyPL: acc.dailyPL + toNumber(holding.daily_pl),
      }),
      { marketValue: 0, totalPL: 0, dailyPL: 0 }
    );
  }, [holdings]);

  return (
    <Box
      sx={{
        p: 2,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderTop: '2px solid',
        borderColor: 'divider',
        backgroundColor: 'background.paper',
      }}
    >
      <Typography variant="subtitle2" fontWeight="bold">
        TOTALS
      </Typography>
      <Stack direction="row" spacing={4}>
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Market Value
          </Typography>
          <Typography variant="body2" fontWeight="bold">
            {formatCurrency(totals.marketValue)}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Total P/L
          </Typography>
          <Typography variant="body2" fontWeight="bold" color={getPLColor(totals.totalPL)}>
            {formatCurrency(totals.totalPL)}
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary" display="block">
            Today's P/L
          </Typography>
          <Typography variant="body2" fontWeight="bold" color={getPLColor(totals.dailyPL)}>
            {formatCurrency(totals.dailyPL)}
          </Typography>
        </Box>
      </Stack>
    </Box>
  );
};

export const HoldingsTable = () => {
  const dispatch = useAppDispatch();
  const { holdings, isLoading, error, filters } = useAppSelector((state) => state.holdings);
  const { accounts } = useAppSelector((state) => state.robinhood);
  const [sortModel, setSortModel] = useState<GridSortModel>([
    { field: 'market_value', sort: 'desc' },
  ]);

  // Fetch holdings when component mounts or filters change, only if accounts exist
  useEffect(() => {
    if (accounts.length > 0) {
      dispatch(fetchHoldings(filters));
    }
  }, [dispatch, filters, accounts.length]);

  const handleRefresh = () => {
    dispatch(fetchHoldings(filters));
  };

  const handleFilterChange = (assetType: string) => {
    // Create new filters object to trigger useEffect
    dispatch(setFilters({ 
      asset_type: assetType as any,
      page: 1,
      page_size: 25,
    }));
  };

  const handleSortModelChange = (model: GridSortModel) => {
    setSortModel(model);
    if (model.length > 0) {
      const { field, sort } = model[0];
      dispatch(setFilters({ ...filters, sort: `${field}:${sort}` }));
    }
  };

  // Define columns with improved styling
  const columns: GridColDef<Holding>[] = [
    {
      field: 'symbol',
      headerName: 'Symbol',
      width: 140,
      renderCell: (params) => (
        <Box>
          <Typography variant="body2" fontWeight="bold">
            {params.row.symbol}
          </Typography>
          {params.row.company_name && (
            <Typography variant="caption" color="text.secondary" noWrap>
              {params.row.company_name}
            </Typography>
          )}
        </Box>
      ),
    },
    {
      field: 'asset_type',
      headerName: 'Type',
      width: 90,
      align: 'center',
      headerAlign: 'center',
      renderCell: (params) => (
        <Chip
          label={params.value.toUpperCase()}
          size="small"
          color={params.value === 'stock' ? 'primary' : params.value === 'option' ? 'secondary' : 'default'}
        />
      ),
    },
    {
      field: 'quantity',
      headerName: 'Shares',
      type: 'number',
      width: 110,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => {
        const num = typeof value === 'string' ? parseFloat(value) : (value || 0);
        return num.toFixed(2);
      },
    },
    {
      field: 'average_cost',
      headerName: 'Avg Cost',
      type: 'number',
      width: 110,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => formatCurrency(value),
    },
    {
      field: 'current_price',
      headerName: 'Price',
      type: 'number',
      width: 110,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => formatCurrency(value),
    },
    {
      field: 'market_value',
      headerName: 'Market Value',
      type: 'number',
      width: 130,
      align: 'right',
      headerAlign: 'right',
      valueFormatter: (value) => formatCurrency(value),
    },
    {
      field: 'total_pl',
      headerName: 'Total P/L',
      width: 140,
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Box textAlign="right">
          <Typography variant="body2" fontWeight="medium" color={getPLColor(params.row.total_pl)}>
            {formatCurrency(params.row.total_pl)}
          </Typography>
          <Typography variant="caption" color={getPLColor(params.row.total_pl_percent)}>
            {formatPercent(params.row.total_pl_percent)}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'daily_pl',
      headerName: "Today's P/L",
      width: 140,
      align: 'right',
      headerAlign: 'right',
      renderCell: (params) => (
        <Box textAlign="right">
          <Typography variant="body2" fontWeight="medium" color={getPLColor(params.row.daily_pl)}>
            {formatCurrency(params.row.daily_pl)}
          </Typography>
          <Typography variant="caption" color={getPLColor(params.row.daily_pl_percent)}>
            {formatPercent(params.row.daily_pl_percent)}
          </Typography>
        </Box>
      ),
    },
    {
      field: 'sector',
      headerName: 'Sector',
      width: 120,
      valueFormatter: (value) => value || 'N/A',
    },
  ];

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6" color="error">
          Error loading holdings: {error}
        </Typography>
        <Button variant="contained" onClick={handleRefresh} sx={{ mt: 2 }}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Controls */}
      <Stack direction="row" spacing={2} sx={{ mb: 2 }} alignItems="center">
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Asset Type</InputLabel>
          <Select
            value={filters.asset_type || 'all'}
            label="Asset Type"
            onChange={(e) => handleFilterChange(e.target.value)}
          >
            <MenuItem value="all">All Assets</MenuItem>
            <MenuItem value="stock">Stocks</MenuItem>
            <MenuItem value="option">Options</MenuItem>
            <MenuItem value="crypto">Crypto</MenuItem>
          </Select>
        </FormControl>

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={isLoading}
        >
          Refresh
        </Button>

        <Box sx={{ flexGrow: 1 }} />

        <Typography variant="body2" color="text.secondary">
          {holdings.length} {holdings.length === 1 ? 'holding' : 'holdings'}
        </Typography>
      </Stack>

      {/* Data Grid */}
      <Paper elevation={0} sx={{ border: 1, borderColor: 'divider' }}>
        <Box sx={{ height: 650, width: '100%' }}>
          <DataGrid
            rows={holdings}
            columns={columns}
            loading={isLoading}
            sortModel={sortModel}
            onSortModelChange={handleSortModelChange}
            pageSizeOptions={[10, 25, 50, 100]}
            initialState={{
              pagination: {
                paginationModel: { pageSize: 25, page: 0 },
              },
            }}
            disableRowSelectionOnClick
            slots={{
              footer: () => <CustomFooter holdings={holdings} />,
            }}
            sx={{
              border: 0,
              '& .MuiDataGrid-cell': {
                py: 1.5,
              },
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: 'action.hover',
                fontWeight: 'bold',
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default HoldingsTable;
