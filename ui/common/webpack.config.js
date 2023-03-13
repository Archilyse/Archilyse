const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const OptimizeCssAssetsPlugin = require('css-minimizer-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyPlugin = require('copy-webpack-plugin');
const Dotenv = require('dotenv-webpack');

// @TODO: Erase babel once we are 100% sure that esbuild-loader works fine

module.exports = {
  target: 'web',
  mode: 'production',
  entry: './src/index.ts',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'index.js',
    library: 'archilyse-ui-components',
    libraryTarget: 'umd',
  },
  cache: {
    type: 'filesystem',
  },
  module: {
    rules: [
      {
        test: /\.s?css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
      },
      {
        test: /\.jsx?$/,
        loader: 'babel-loader',
        options: {
          cacheDirectory: true,
        },
        exclude: [path.resolve(__dirname, 'node_modules'), path.resolve(__dirname, 'assets')],
      },
      {
        test: /\.tsx?$/,
        loader: 'ts-loader',
        exclude: [path.resolve(__dirname, '../node_modules'), path.resolve(__dirname, 'node_modules')],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/inline',
      },
    ],
  },
  resolve: {
    modules: [path.resolve(__dirname, '../node_modules'), path.resolve(__dirname, 'node_modules')],
    extensions: ['.ts', '.tsx', '.js'],
  },
  externals: [
    {
      react: 'react',
      'react-dom': 'ReactDOM',
    },
    /@material-ui\/.*/,
  ],
  plugins: [
    new Dotenv({ path: '../../docker/.env' }),
    new CleanWebpackPlugin(),
    new CopyPlugin({
      patterns: [{ from: path.resolve(__dirname, 'src/theme.scss'), to: path.resolve(__dirname, 'dist') }],
    }),
    new MiniCssExtractPlugin({ filename: 'styles.css' }),
    new OptimizeCssAssetsPlugin(),
  ],
};
